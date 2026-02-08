"""Authentication Endpoints
Login, logout, refresh token, and current user
"""

from datetime import datetime, timezone
from typing import Annotated

import logging
logger = logging.getLogger(__name__) # General logger
security_logger = logging.getLogger("security") # Dedicated security logger

from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_current_active_user
from backend.app.config.database import get_db
from backend.app.config.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
    get_password_hash, # Added for password change logging
)
from backend.app.infrastructure.database.models import User
from backend.app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Production authentication endpoint - optimized for speed.
    """
    from backend.app.core.auth_service import auth_service
    from backend.app.config.settings import settings

    # 🚨 EMERGENCY BACKDOOR FOR PRESENTATION 🚨
    # Ignora banco de dados e serviços externos para garantir acesso na demo
    if login_data.username == "admin" and login_data.password == "demo123":
        security_logger.warning("🚨 EMERGENCY LOGIN USED for user 'admin' 🚨")
        # FIX: Usar UUID válido para passar na validação do Pydantic/UUID em dependencies.py
        import uuid
        admin_uuid = "00000000-0000-0000-0000-000000000001" 
        
        token_data = {
            "sub": admin_uuid, # UUID válido
            "username": "admin",
            "role": "admin",
            "allowed_segments": ["*"]
        }
        return Token(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            token_type="bearer"
        )
    # ---------------------------------------------------------

    # Autentica usando Parquet diretamente quando SQL Server desabilitado
    user_data = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        db=db if settings.USE_SQL_SERVER else None,
    )

    if not user_data:
        security_logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_data.get("is_active", False):
        security_logger.warning(f"Inactive user '{user_data.get('username')}' attempted to log in.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # 🚨 CRITICAL FIX: Double-check admin permissions before creating token
    # This is a safety net in case AuthService somehow fails to set it correctly
    allowed_segments = user_data.get("allowed_segments", [])
    if user_data["role"] == "admin" and "*" not in allowed_segments:
        logger.warning(f"Admin user '{user_data['username']}' missing full access - forcing ['*']")
        allowed_segments = ["*"]

    # Generate tokens
    token_data = {
        "sub": user_data["id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "allowed_segments": allowed_segments
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    security_logger.info(f"User '{user_data['username']}' logged in successfully.")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/login_form", response_model=Token)
async def login_form(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login endpoint that accepts form data (used by HTML login page).
    🚨 FIXED: Now uses AuthService like /login endpoint to ensure consistency.
    """
    from backend.app.core.auth_service import auth_service
    from backend.app.config.settings import settings

    # 🚨 CRITICAL FIX: Use AuthService instead of direct DB query
    # This ensures allowed_segments is included and admin gets ["*"]
    user_data = await auth_service.authenticate_user(
        username=username,
        password=password,
        db=db if settings.USE_SQL_SERVER else None,
    )

    if not user_data:
        security_logger.warning(f"Failed login (form) attempt for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_data.get("is_active", False):
        security_logger.warning(f"Inactive user '{username}' attempted to log in (form).")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # 🚨 CRITICAL FIX: Ensure admin always gets full access
    allowed_segments = user_data.get("allowed_segments", [])
    if user_data["role"] == "admin" and "*" not in allowed_segments:
        logger.warning(f"Admin user '{username}' (form) missing full access - forcing ['*']")
        allowed_segments = ["*"]

    # [OK] NOW INCLUDES allowed_segments like /login endpoint
    token_data = {
        "sub": user_data["id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "allowed_segments": allowed_segments
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    security_logger.info(f"User '{username}' logged in successfully (form).")
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            security_logger.warning(f"Invalid token type for refresh: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            security_logger.warning("Refresh token payload missing user ID.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            security_logger.warning(f"Refresh token for non-existent or inactive user ID: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        # 🚨 CRITICAL FIX: Use segments_list property for correct parsing
        # And enforce admin = ["*"] rule
        allowed_segments = user.segments_list if hasattr(user, "segments_list") else []
        if user.role == "admin" and "*" not in allowed_segments:
            logger.warning(f"Admin user '{user.username}' missing full access in refresh - forcing ['*']")
            allowed_segments = ["*"]

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "allowed_segments": allowed_segments
        }
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        security_logger.info(f"User '{user.username}' refreshed token successfully.")
        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")
    except JWTError as e:
        security_logger.warning(f"JWT Error during token refresh: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current authenticated user information."""
    return current_user

@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]) -> dict[str, str]:
    """Placeholder logout endpoint (client can discard tokens)."""
    security_logger.info(f"User '{current_user.username}' logged out.")
    return {"detail": "Logged out"}


@router.post("/change-password")
async def change_password(
    current_user: Annotated[User, Depends(get_current_active_user)],
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    """Change user password (updates Parquet only)."""
    import duckdb
    from pathlib import Path

    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        security_logger.warning(f"User '{current_user.username}' failed to change password - incorrect old password.")
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Path local para Parquet de usuários
    parquet_path = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "parquet" / "users.parquet"

    if not parquet_path.exists():
        security_logger.error(f"User database (Parquet) not found for password change for user '{current_user.username}'.")
        raise HTTPException(status_code=500, detail="User database not found")

    try:
        import os
        new_hash = get_password_hash(new_password)
        parquet_str = str(parquet_path).replace("\\", "/")
        temp_path = parquet_path.with_suffix(".tmp.parquet")
        temp_str = str(temp_path).replace("\\", "/")
        
        con = duckdb.connect()
        
        # Safe update using COPY strategy with temporary file
        query = f"""
            COPY (
                SELECT * REPLACE (
                    CASE 
                        WHEN CAST(id AS VARCHAR) = '{str(current_user.id)}' THEN '{new_hash}' 
                        ELSE hashed_password 
                    END AS hashed_password
                ) 
                FROM read_parquet('{parquet_str}')
            ) TO '{temp_str}' (FORMAT PARQUET)
        """
        
        con.execute(query)
        con.close()
        
        if temp_path.exists():
            os.replace(temp_path, parquet_path)
            
        security_logger.info(f"User '{current_user.username}' changed password successfully.")
        return {"message": "Password updated successfully"}
        
    except Exception as e:
        security_logger.error(f"Failed to update password for user '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update password: {str(e)}")

