"""
Supabase User Management Service
Handles user CRUD operations with Supabase Auth + user_profiles table
"""

import logging
from typing import Optional
from datetime import datetime

# Use ADMIN client for user management (requires service_role key)
from app.core.supabase_client import get_supabase_admin_client
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class SupabaseUserService:
    """Service for managing users in Supabase"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load Supabase ADMIN client only when needed"""
        if self._client is None:
            if not settings.USE_SUPABASE_AUTH:
                raise ValueError(
                    "Supabase authentication is disabled. "
                    "This service requires USE_SUPABASE_AUTH=true in .env"
                )
            # Use ADMIN client with service_role key for user management
            self._client = get_supabase_admin_client()
        return self._client

    def create_user(
        self,
        email: str,
        password: str,
        username: str,
        role: str = "user",
        full_name: Optional[str] = None,
        allowed_segments: Optional[list[str]] = None
    ) -> dict:
        """
        Create a new user in Supabase Auth and user_profiles table

        Args:
            email: User's email
            password: User's password
            username: Username for the system
            role: User role (admin, user, viewer)
            full_name: Optional full name
            allowed_segments: List of allowed segments

        Returns:
            Dictionary with user data

        Raises:
            Exception if user creation fails
        """
        try:
            # 1. Create user in Supabase Auth
            auth_response = self.client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "username": username,
                    "role": role,
                    "full_name": full_name or username,
                    "allowed_segments": allowed_segments or []
                }
            })

            if not auth_response.user:
                raise Exception("Failed to create user in Supabase Auth")

            user_id = auth_response.user.id

            # 2. Create profile in user_profiles table
            profile_data = {
                "id": str(user_id),
                "username": username,
                "role": role,
                "full_name": full_name or username,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            profile_response = self.client.table("user_profiles").insert(profile_data).execute()

            security_logger.info(f"User '{username}' created successfully in Supabase (ID: {user_id})")

            return {
                "id": str(user_id),
                "email": email,
                "username": username,
                "role": role,
                "full_name": full_name or username,
                "allowed_segments": allowed_segments or [],
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            security_logger.error(f"Failed to create user '{username}': {e}\n{error_details}")
            raise Exception(f"Failed to create user: {str(e)}")

    def list_users(self, limit: int = 100) -> list[dict]:
        """
        List all users from Supabase

        Args:
            limit: Maximum number of users to return

        Returns:
            List of user dictionaries
        """
        try:
            # Get users from user_profiles table (which links to auth.users)
            response = self.client.table("user_profiles").select("*").limit(limit).execute()

            users = []
            for profile in response.data:
                # Get auth user data to check email and status
                try:
                    auth_user = self.client.auth.admin.get_user_by_id(profile["id"])
                    email = auth_user.user.email if auth_user.user else "N/A"
                    # Check if user is banned - the attribute may vary by Supabase version
                    is_active = True
                    if auth_user.user:
                        # Try different attribute names for banned status
                        if hasattr(auth_user.user, 'banned_until') and auth_user.user.banned_until:
                            is_active = False
                        elif hasattr(auth_user.user, 'is_banned') and auth_user.user.is_banned:
                            is_active = False
                    # Get allowed_segments from metadata
                    user_metadata = auth_user.user.user_metadata or {}
                    allowed_segments = user_metadata.get("allowed_segments", [])
                    logger.info(f"User {profile['id']}: email={email}, segments={allowed_segments}")
                except Exception as e:
                    logger.warning(f"Failed to get auth user data for {profile['id']}: {e}")
                    email = "N/A"
                    is_active = True
                    allowed_segments = []

                users.append({
                    "id": profile["id"],
                    "username": profile.get("username", "N/A"),
                    "email": email,
                    "role": profile.get("role", "user"),
                    "full_name": profile.get("full_name", ""),
                    "allowed_segments": allowed_segments,
                    "is_active": is_active,
                    "created_at": profile.get("created_at", ""),
                    "updated_at": profile.get("updated_at", "")
                })

            logger.info(f"Listed {len(users)} users from Supabase")
            return users

        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []

    def get_user(self, user_id: str) -> Optional[dict]:
        """
        Get a single user by ID

        Args:
            user_id: User's UUID

        Returns:
            User dictionary or None if not found
        """
        try:
            # Get profile
            profile_response = self.client.table("user_profiles").select("*").eq("id", user_id).execute()

            if not profile_response.data:
                return None

            profile = profile_response.data[0]

            # Get auth user data
            auth_user = self.client.auth.admin.get_user_by_id(user_id)
            email = auth_user.user.email if auth_user.user else "N/A"
            
            # Safe access to banned_until
            banned_until = getattr(auth_user.user, "banned_until", None)
            is_active = not banned_until if auth_user.user else True
            
            user_metadata = auth_user.user.user_metadata or {}
            allowed_segments = user_metadata.get("allowed_segments", [])

            return {
                "id": profile["id"],
                "username": profile.get("username", "N/A"),
                "email": email,
                "role": profile.get("role", "user"),
                "full_name": profile.get("full_name", ""),
                "allowed_segments": allowed_segments,
                "is_active": is_active,
                "created_at": profile.get("created_at", ""),
                "updated_at": profile.get("updated_at", "")
            }

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
        role: Optional[str] = None,
        full_name: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
        allowed_segments: Optional[list[str]] = None
    ) -> dict:
        """
        Update user in Supabase Auth and user_profiles

        Args:
            user_id: User's UUID
            email: New email (optional)
            username: New username (optional)
            role: New role (optional)
            full_name: New full name (optional)
            password: New password (optional)
            is_active: Active status (optional)
            allowed_segments: New allowed segments (optional)

        Returns:
            Updated user dictionary

        Raises:
            Exception if update fails
        """
        try:
            # Update auth user if needed
            auth_updates = {}
            user_metadata_updates = {}
            
            if email:
                auth_updates["email"] = email
            if password:
                auth_updates["password"] = password
            if is_active is not None:
                # Ban/unban user based on is_active
                if not is_active:
                    auth_updates["ban_duration"] = "876000h"  # ~100 years (effectively permanent)
                else:
                    auth_updates["ban_duration"] = "none"
            
            # Update metadata
            if username:
                user_metadata_updates["username"] = username
            if role:
                user_metadata_updates["role"] = role
            if full_name:
                user_metadata_updates["full_name"] = full_name
            if allowed_segments is not None:
                user_metadata_updates["allowed_segments"] = allowed_segments

            if user_metadata_updates:
                auth_updates["user_metadata"] = user_metadata_updates

            if auth_updates:
                self.client.auth.admin.update_user_by_id(user_id, auth_updates)

            # Update profile
            profile_updates = {"updated_at": datetime.utcnow().isoformat()}
            if username:
                profile_updates["username"] = username
            if role:
                profile_updates["role"] = role
            if full_name:
                profile_updates["full_name"] = full_name

            self.client.table("user_profiles").update(profile_updates).eq("id", user_id).execute()

            security_logger.info(f"User {user_id} updated successfully")

            # Return updated user
            return self.get_user(user_id)

        except Exception as e:
            security_logger.error(f"Failed to update user {user_id}: {e}")
            raise Exception(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user from Supabase Auth and user_profiles

        Args:
            user_id: User's UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from user_profiles first
            self.client.table("user_profiles").delete().eq("id", user_id).execute()

            # Delete from auth
            self.client.auth.admin.delete_user(user_id)

            security_logger.info(f"User {user_id} deleted successfully")
            return True

        except Exception as e:
            security_logger.error(f"Failed to delete user {user_id}: {e}")
            return False


# Global instance
supabase_user_service = SupabaseUserService()
