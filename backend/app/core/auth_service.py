import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import json # Import json

import duckdb
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config.settings import get_settings
from backend.app.infrastructure.database.models import User

settings = get_settings()
logger = logging.getLogger(__name__) # General logger
security_logger = logging.getLogger("security") # Dedicated security logger


class AuthService:
    """
    Authentication service with intelligent fallback.

    Priority:
    1. SQL Server (if USE_SQL_SERVER=true and available)
    2. Parquet (fallback or when SQL Server disabled)
    """

    def __init__(self):
        self.use_sql_server = settings.USE_SQL_SERVER
        self.use_supabase = settings.USE_SUPABASE_AUTH

        # Path Resolution for users.parquet
        # Priority:
        # 1. backend/data/parquet/users.parquet (deploy/docker structure often)
        # 2. data/parquet/users.parquet (local root structure)
        # 3. backend/app/data/parquet/users.parquet (legacy)
        
        base_dir = Path(__file__).parent.parent.parent.parent # Root or Backend depending on execution
        
        # We need to find the Project Root. 
        # If __file__ is backend/app/core/auth_service.py
        # parentx4 is C:\Agente_BI\BI_Solution (Project Root)
        
        possible_paths = [
            base_dir / "backend" / "data" / "parquet" / "users.parquet",
            base_dir / "data" / "parquet" / "users.parquet",
            base_dir / "backend" / "app" / "data" / "parquet" / "users.parquet"
        ]
        
        self.parquet_path = possible_paths[1] # Default to root/data (legacy behavior)
        
        for p in possible_paths:
            if p.exists():
                self.parquet_path = p
                logger.info(f"AuthService: Using users.parquet at {p}")
                break
        
        if not self.parquet_path.exists():
            logger.warning(f"AuthService: users.parquet NOT FOUND in any expected location. Auth may fail.")

    async def authenticate_user(
        self,
        username: str,
        password: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[dict]:
        """
        Authenticate user with hybrid approach.

        Priority:
        1. Supabase (if USE_SUPABASE_AUTH=true)
        2. Parquet (fallback or when Supabase disabled)
        3. SQL Server (last resort)

        Args:
            username: User's username or email
            password: User's plain text password
            db: Optional database session (used when SQL Server is enabled)

        Returns:
            User dict if authenticated, None otherwise
        """
        user_data = None

        # Priority 1: Supabase Auth (if enabled)
        if self.use_supabase:
            try:
                # For Supabase, username should be an email
                user_data = await self._auth_from_supabase(username, password, db)
                if user_data:
                    security_logger.info(f"User '{username}' authenticated via Supabase")
                    return user_data
            except Exception as e:
                security_logger.warning(f"Supabase auth failed for '{username}': {e}")

        # Priority 2: Parquet (fallback or primary if Supabase disabled)
        try:
            user_data = await self._auth_from_parquet(username, password)
            if user_data:
                security_logger.info(f"User '{username}' authenticated via Parquet")
                return user_data
        except Exception as e:
            security_logger.error(f"Parquet auth failed for '{username}': {e}")

        # Priority 3: SQL Server (last resort)
        # 🚨 OPTIMIZATION: Only attempt SQL if explicitly enabled AND DB session provided AND configured
        if self.use_sql_server and db is not None and settings.DATABASE_URL:
            try:
                user_data = await self._auth_from_sql(username, password, db)
                if user_data:
                    security_logger.info(f"User '{username}' authenticated via SQL Server")
                    return user_data
            except Exception as e:
                security_logger.warning(f"SQL Server auth failed for '{username}': {e}")
        elif self.use_sql_server and db is None:
             security_logger.warning(f"Skipping SQL Server auth for '{username}': DB session not available (check db dependency)")

        security_logger.warning(f"Authentication failed for user '{username}' - Invalid credentials or inactive.")
        return None

    async def _auth_from_sql(
        self,
        username: str,
        password: str,
        db: AsyncSession
    ) -> Optional[dict]:
        """Authenticate from SQL Server"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            security_logger.warning(f"User '{username}' not found in SQL Server.")
            return None

        # Verify password
        if not self._verify_password(password, user.hashed_password):
            security_logger.warning(f"Invalid password attempt for user '{username}' in SQL Server.")
            return None

        # Check if active
        if not user.is_active:
            security_logger.warning(f"Inactive user '{username}' attempted to log in via SQL Server.")
            return None

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        # Parse allowed_segments
        allowed_segments = []
        role = user.role

        if user.allowed_segments:
            try:
                allowed_segments = json.loads(user.allowed_segments)
            except Exception as e:
                security_logger.warning(f"Failed to parse allowed_segments for '{username}' from SQL: {e}")
                allowed_segments = []

        # 🚨 CRITICAL FIX: Admin ALWAYS gets full access (SQL Server path)
        if role == "admin":
            allowed_segments = ["*"]
            security_logger.info(f"Admin user '{username}' (SQL Server) granted full access (allowed_segments=['*'])")

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email or "",
            "role": role,
            "is_active": user.is_active,
            "allowed_segments": allowed_segments
        }

    async def _auth_from_supabase(
        self,
        email: str,  # Changed from username to email
        password: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[dict]:
        """Authenticate from Supabase Auth using email"""
        try:
            from backend.app.core.supabase_client import get_supabase_client
            from supabase import AuthApiError

            try:
                supabase = get_supabase_client()
            except ValueError as ve:
                security_logger.error(f"Supabase client not configured: {ve}")
                return None

            # Authenticate with Supabase using email directly
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
            except AuthApiError as auth_err:
                security_logger.warning(f"Supabase auth failed for '{email}': {auth_err}")
                return None

            # Check response
            if not response or not response.session or not response.session.user:
                security_logger.warning(f"Supabase auth failed: no user/session returned for '{email}'")
                return None

            user = response.session.user
            user_id = str(user.id)

            # [DEBUG] FIX: Authorization logic based on USE_SQL_SERVER setting
            role = "user"
            allowed_segments = []

            if self.use_sql_server and db:
                # Option 1: SQL Server is enabled and DB session was passed
                # Get role and segments from SQL Server
                try:
                    from sqlalchemy import text
                    import json

                    result = await db.execute(
                        select(User).where(User.id == user.id)
                    )
                    db_user = result.scalar_one_or_none()
                    if db_user:
                        role = db_user.role
                        if db_user.allowed_segments:
                            try:
                                allowed_segments = json.loads(db_user.allowed_segments)
                            except:
                                allowed_segments = []
                        security_logger.info(f"Permissions for '{email}' loaded from SQL Server")
                except Exception as e:
                    security_logger.error(f"Failed to fetch permissions from SQL Server for '{email}': {e}")

            else:
                # Option 2: SQL Server disabled OR db session not available
                # Get role from Supabase user_profiles table
                
                # Retrieve metadata first as it might contain allowed_segments regardless of profile
                user_metadata = user.user_metadata or {}
                if "allowed_segments" in user_metadata:
                    try:
                        allowed_segments = user_metadata["allowed_segments"]
                        # Ensure it's a list
                        if isinstance(allowed_segments, str):
                            allowed_segments = json.loads(allowed_segments)
                        if not isinstance(allowed_segments, list):
                            allowed_segments = []
                    except Exception as e:
                        security_logger.warning(f"Failed to parse allowed_segments from metadata for '{email}': {e}")
                        allowed_segments = []
                
                try:
                    profile_resp = supabase.table("user_profiles").select("role, username").eq("id", user_id).execute()
                    if profile_resp.data:
                        role = profile_resp.data[0].get("role", "user")
                        security_logger.info(f"User '{email}' role loaded from Supabase user_profiles: {role}")
                    else:
                        security_logger.warning(f"No profile found for '{email}' in user_profiles table. Falling back to metadata.")
                        # Fallback to user_metadata
                        role = user_metadata.get("role", "user")
                        
                except Exception as profile_error:
                    security_logger.error(f"Could not fetch profile from Supabase for '{email}': {profile_error}")
                    # Fallback to user_metadata (LESS SECURE)
                    role = user_metadata.get("role", "user")

            # 🚨 CRITICAL FIX: Admin ALWAYS gets full access (Supabase path)
            if role == "admin":
                allowed_segments = ["*"]
                security_logger.info(f"Admin user '{email}' (Supabase) granted full access (allowed_segments=['*'])")

            return {
                "id": user_id,
                "username": user.email.split('@')[0],  # Extract username from email
                "email": user.email,
                "role": role,
                "is_active": True,
                "allowed_segments": allowed_segments
            }

        except Exception as e:
            security_logger.error(f"Supabase authentication error for '{email}': {e}")
            return None

    async def _auth_from_parquet(
        self,
        username: str,
        password: str
    ) -> Optional[dict]:
        """Authenticate from Parquet file"""
        # logger.info(f"Password received length: {len(password)}") # Removed sensitive logging
        
        if not self.parquet_path.exists():
            security_logger.error(f"Parquet file not found for authentication: {self.parquet_path}")
            return None

        try:
            # Query DuckDB directly (more efficient than loading whole DF)
            parquet_str = str(self.parquet_path).replace("\\", "/")
            
            # Use ephemeral connection
            con = duckdb.connect()
            # Prepare query - simple parameterized query
            result = con.execute(f"SELECT * FROM read_parquet('{parquet_str}') WHERE username = ?", [username]).fetchall()

            if not result:
                security_logger.warning(f"User '{username}' not found in Parquet.")
                return None

            # Map columns to values
            columns = [desc[0] for desc in con.description]
            user_row = dict(zip(columns, result[0]))
            
            security_logger.info(f"User '{username}' found in Parquet. Verifying password...")

            # Verify password
            hashed_password = user_row["hashed_password"]
            is_valid = self._verify_password(password, hashed_password)
            
            if not is_valid:
                security_logger.warning(f"Invalid password attempt for user '{username}' in Parquet.")
                return None
            
            security_logger.info(f"Password verified for '{username}' in Parquet.")

            # Check if active
            if not user_row.get("is_active", True):
                security_logger.warning(f"Inactive user '{username}' attempted to log in via Parquet.")
                return None

            # Parse allowed_segments
            allowed_segments = []
            role = user_row["role"]

            if "allowed_segments" in user_row and user_row["allowed_segments"]:
                try:
                    # It should be a JSON string
                    allowed_segments = json.loads(user_row["allowed_segments"])
                except Exception as e:
                    # Fallback if it's not JSON (e.g. legacy data)
                    security_logger.warning(f"Failed to parse allowed_segments for '{username}': {e}")
                    allowed_segments = []

            # 🚨 CRITICAL FIX: Admin ALWAYS gets full access
            # Regardless of what's stored in DB, admin role = all segments
            if role == "admin":
                allowed_segments = ["*"]
                security_logger.info(f"Admin user '{username}' granted full access (allowed_segments=['*'])")

            return {
                "id": str(user_row["id"]),
                "username": user_row["username"],
                "email": user_row.get("email", ""),
                "role": role,
                "is_active": user_row.get("is_active", True),
                "allowed_segments": allowed_segments
            }
        except Exception as e:
            security_logger.error(f"Error reading/processing Parquet for user '{username}': {e}")
            return None

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password using bcrypt"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            security_logger.error(f"Password verification error for provided hash: {e}")
            return False


# Global instance
auth_service = AuthService()
