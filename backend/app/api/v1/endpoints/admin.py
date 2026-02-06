"""
Admin Endpoints
User management, audit logs, and system settings
"""

import uuid
import json # Added import
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.dependencies import get_db, require_role, get_current_active_user
from app.config.security import get_password_hash
from app.infrastructure.database.models import AuditLog, Report, User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.parquet_cache import cache
from app.core.sync_service import sync_service
from app.core.supabase_user_service import supabase_user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


# Modelos adicionais para compatibilidade
class AdminStats(BaseModel):
    totalUsers: int
    activeUsers: int
    totalQueries: int
    systemHealth: str


@router.post("/sync-parquet")
async def sync_parquet_data(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """
    Trigger SQL Server -> Parquet synchronization
    
    Runs in background. Requires admin role.
    """
    background_tasks.add_task(sync_service.run_sync)
    return {"message": "Sincronização iniciada em segundo plano. Verifique os logs para progresso.", "status": "processing"}


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AdminStats:
    """
    Get system statistics

    Returns admin dashboard metrics with real data from Parquet.
    Requires admin role.
    """
    import polars as pl
    import logging

    logger = logging.getLogger(__name__)

    # Verificar se é admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Contar usuários no banco
        try:
            result = await db.execute(select(func.count(User.id)))
            total_users = result.scalar()

            result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
            active_users = result.scalar()
        except:
            # Fallback para Parquet se SQL falhar
            df_users = cache.get_dataframe("users.parquet")
            total_users = len(df_users)
            active_users = df_users.filter(pl.col("is_active") == True).height

        # Estatísticas de dados do sistema
        df_admmat = cache.get_dataframe("admmat.parquet")
        total_queries = df_admmat.filter(pl.col("VENDA_30DD") > 0).height

        logger.info(f"Admin stats: {total_users} users, {total_queries} active products")

        return AdminStats(
            totalUsers=total_users or 0,
            activeUsers=active_users or 0,
            totalQueries=total_queries,
            systemHealth="healthy"
        )

    except Exception as e:
        logger.error(f"Error fetching admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/users")
async def get_users(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """
    Get all users from Supabase

    Returns list of users with their profiles and auth status.
    Requires admin role.
    """
    from app.config.settings import settings

    if settings.USE_SUPABASE_AUTH:
        # Use Supabase user service
        users = supabase_user_service.list_users(limit=1000)
        return users
    else:
        # Fallback to SQL Server (legacy)
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()
        return [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email or "",
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else "",
                "updated_at": user.updated_at.isoformat() if user.updated_at else "",
            }
            for user in users
        ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
) -> User:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Create new user in Supabase Auth + user_profiles

    Creates user with auto-confirmed email and profile data.
    Requires admin role.
    """
    from app.config.settings import settings

    if settings.USE_SUPABASE_AUTH:
        try:
            # Create user in Supabase
            new_user = supabase_user_service.create_user(
                email=user_data.email,
                password=user_data.password,
                username=user_data.username,
                role=user_data.role,
                full_name=user_data.username,  # Can be enhanced later
                allowed_segments=user_data.allowed_segments # Added allowed_segments
            )
            
            # --- SYNC WITH SQL SERVER (AUTHORIZATION) ---
            # Ensure the user exists locally for permissions/segments check
            try:
                # Check if user exists locally (by ID or Username)
                user_id = uuid.UUID(new_user["id"])
                
                result = await db.execute(select(User).where(User.id == user_id))
                local_user = result.scalar_one_or_none()
                
                if not local_user:
                    # Create local user record
                    hashed_dummy = "EXTERNAL_AUTH_SUPABASE" 
                    local_user = User(
                        id=user_id,
                        username=user_data.username,
                        email=user_data.email,
                        hashed_password=hashed_dummy,
                        role=user_data.role,
                        is_active=True,
                        allowed_segments=json.dumps(user_data.allowed_segments) if user_data.allowed_segments else "[]"
                    )
                    db.add(local_user)
                else:
                    # Update existing local user
                    local_user.username = user_data.username
                    local_user.email = user_data.email
                    local_user.role = user_data.role
                    if user_data.allowed_segments is not None:
                        local_user.allowed_segments = json.dumps(user_data.allowed_segments)
                
                await db.commit()
            except Exception as e:
                # Log error but don't fail the request (Supabase creation worked)
                # logger.error(f"Failed to sync new user to SQL Server: {e}")
                print(f"Failed to sync new user to SQL Server: {e}")

            return new_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        # Fallback to SQL Server (legacy)
        result = await db.execute(
            select(User).where(
                (User.username == user_data.username) | (User.email == user_data.email)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role,
            allowed_segments=json.dumps(user_data.allowed_segments) if user_data.allowed_segments else "[]" # Added allowed_segments
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {
            "id": str(new_user.id),
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "allowed_segments": user_data.allowed_segments
        }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Update user in Supabase

    Updates user auth data and profile information.
    Requires admin role.
    """
    from app.config.settings import settings

    if settings.USE_SUPABASE_AUTH:
        try:
            update_data = user_data.model_dump(exclude_unset=True)

            updated_user = supabase_user_service.update_user(
                user_id=user_id,
                email=update_data.get("email"),
                username=update_data.get("username"),
                role=update_data.get("role"),
                password=update_data.get("password"),
                is_active=update_data.get("is_active"),
                allowed_segments=update_data.get("allowed_segments") # Added allowed_segments
            )

            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # --- SYNC WITH SQL SERVER (AUTHORIZATION) ---
            try:
                # Check if user exists locally
                u_id = uuid.UUID(user_id)
                result = await db.execute(select(User).where(User.id == u_id))
                local_user = result.scalar_one_or_none()
                
                if local_user:
                    if "username" in update_data: local_user.username = update_data["username"]
                    if "email" in update_data: local_user.email = update_data["email"]
                    if "role" in update_data: local_user.role = update_data["role"]
                    if "is_active" in update_data: local_user.is_active = update_data["is_active"]
                    if "allowed_segments" in update_data: 
                        local_user.allowed_segments = json.dumps(update_data["allowed_segments"])
                    
                    await db.commit()
            except Exception as e:
                print(f"Failed to sync updated user to SQL Server: {e}")

            return updated_user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        # Fallback to SQL Server (legacy)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        # Handle allowed_segments conversion for SQL Server
        if "allowed_segments" in update_data:
            user.allowed_segments = json.dumps(update_data.pop("allowed_segments"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "allowed_segments": json.loads(user.allowed_segments) if user.allowed_segments else []
        }


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Delete user from Supabase

    Removes user from auth and profile tables.
    Requires admin role. Cannot delete self.
    """
    from app.config.settings import settings

    # Prevent self-deletion
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    if settings.USE_SUPABASE_AUTH:
        success = supabase_user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or deletion failed"
            )
    else:
        # Fallback to SQL Server (legacy)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await db.delete(user)
        await db.commit()


@router.get("/audit-logs")
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
    limit: int = 100,
) -> list[dict]:
    """Get audit logs"""
    
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    
    # Get user names
    user_ids = {log.user_id for log in logs}
    users_result = await db.execute(
        select(User.id, User.username).where(User.id.in_(user_ids))
    )
    users_map = {user_id: username for user_id, username in users_result}
    
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "user_name": users_map.get(log.user_id, "Unknown"),
            "action": log.action,
            "resource": log.resource,
            "details": log.details,
            "ip_address": str(log.ip_address),
            "timestamp": log.timestamp.isoformat(),
            "status": log.status,
        }
        for log in logs
    ]