"""
Admin Endpoints
User management, audit logs, and system settings
"""

import uuid
import json # Added import
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from backend.app.api.dependencies import get_db, require_role, get_current_active_user
from backend.app.config.security import get_password_hash
from backend.app.infrastructure.database.models import AuditLog, Report, User, UserPreference
from backend.app.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.app.core.parquet_cache import cache
from backend.app.core.sync_service import sync_service
from backend.app.core.supabase_user_service import supabase_user_service
from backend.app.core.playground_sql_access import build_sql_access_context, evaluate_sql_access, parse_sql_access_context

router = APIRouter(prefix="/admin", tags=["Admin"])
PLAYGROUND_SQL_ACCESS_KEY = "playground_sql_full_access"
PLAYGROUND_CANARY_ACCESS_KEY = "playground_canary_access"
PLAYGROUND_ACCESS_KEY = "playground_access"


# Modelos adicionais para compatibilidade
class AdminStats(BaseModel):
    totalUsers: int
    activeUsers: int
    totalQueries: int
    systemHealth: str


class PlaygroundSqlAccessUpdate(BaseModel):
    enabled: bool
    expires_at: str | None = None


class PlaygroundSqlAccessItem(BaseModel):
    user_id: str
    enabled: bool
    active: bool
    expires_at: str | None = None


class PlaygroundCanaryAccessUpdate(BaseModel):
    enabled: bool


class PlaygroundCanaryAccessItem(BaseModel):
    user_id: str
    enabled: bool


class PlaygroundAccessUpdate(BaseModel):
    enabled: bool


class PlaygroundAccessItem(BaseModel):
    user_id: str
    enabled: bool


def _invalidate_playground_sql_cache(user_id: str | None = None) -> None:
    try:
        from backend.app.api.v1.endpoints import playground as playground_endpoint
        if user_id:
            playground_endpoint._sql_access_cache.pop(str(user_id), None)
        else:
            playground_endpoint._sql_access_cache.clear()
    except Exception:
        # Falha de invalidação não deve quebrar endpoint administrativo.
        pass


def _invalidate_playground_canary_cache(user_id: str | None = None) -> None:
    try:
        from backend.app.api.v1.endpoints import playground as playground_endpoint
        if user_id:
            playground_endpoint._canary_access_cache.pop(str(user_id), None)
        else:
            playground_endpoint._canary_access_cache.clear()
    except Exception:
        pass


def _invalidate_playground_access_cache(user_id: str | None = None) -> None:
    try:
        from backend.app.api.v1.endpoints import playground as playground_endpoint
        if user_id:
            playground_endpoint._playground_access_cache.pop(str(user_id), None)
        else:
            playground_endpoint._playground_access_cache.clear()
    except Exception:
        pass


def _log_sql_access_change(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    target_user_id: uuid.UUID | None,
    enabled: bool,
    expires_at: str | None,
    action: str,
) -> None:
    details = {
        "target_user_id": str(target_user_id) if target_user_id else None,
        "enabled": enabled,
        "expires_at": expires_at,
    }
    db.add(
        AuditLog(
            user_id=actor_user_id,
            action=action,
            resource="playground_sql_access",
            details=details,
            ip_address="admin-panel",
            status="success",
        )
    )


def _log_canary_access_change(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    target_user_id: uuid.UUID | None,
    enabled: bool,
    action: str,
) -> None:
    details = {
        "target_user_id": str(target_user_id) if target_user_id else None,
        "enabled": enabled,
    }
    db.add(
        AuditLog(
            user_id=actor_user_id,
            action=action,
            resource="playground_canary_access",
            details=details,
            ip_address="admin-panel",
            status="success",
        )
    )


def _log_playground_access_change(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    target_user_id: uuid.UUID | None,
    enabled: bool,
    action: str,
) -> None:
    details = {
        "target_user_id": str(target_user_id) if target_user_id else None,
        "enabled": enabled,
    }
    db.add(
        AuditLog(
            user_id=actor_user_id,
            action=action,
            resource="playground_access",
            details=details,
            ip_address="admin-panel",
            status="success",
        )
    )


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
    from backend.app.config.settings import settings

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


@router.get("/playground-sql-access", response_model=list[PlaygroundSqlAccessItem])
async def list_playground_sql_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlaygroundSqlAccessItem]:
    result = await db.execute(
        select(UserPreference).where(UserPreference.key == PLAYGROUND_SQL_ACCESS_KEY)
    )
    rows = result.scalars().all()
    items: list[PlaygroundSqlAccessItem] = []
    for row in rows:
        parsed_ctx = parse_sql_access_context(row.context)
        is_active, _ = evaluate_sql_access(str(row.value), row.context)
        items.append(
            PlaygroundSqlAccessItem(
                user_id=str(row.user_id),
                enabled=str(row.value).lower() == "true",
                active=is_active,
                expires_at=parsed_ctx.get("expires_at"),
            )
        )
    return items


@router.put("/playground-sql-access/{user_id}", response_model=PlaygroundSqlAccessItem)
async def update_playground_sql_access(
    user_id: str,
    payload: PlaygroundSqlAccessUpdate,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaygroundSqlAccessItem:
    try:
        target_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id inválido")

    expires_at_value: datetime | None = None
    if payload.enabled and payload.expires_at:
        try:
            expires_at_value = datetime.fromisoformat(payload.expires_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="expires_at inválido (use ISO-8601)")

    pref_result = await db.execute(
        select(UserPreference).where(
            (UserPreference.user_id == target_user_id)
            & (UserPreference.key == PLAYGROUND_SQL_ACCESS_KEY)
        )
    )
    preference = pref_result.scalar_one_or_none()
    if preference is None:
        preference = UserPreference(
            user_id=target_user_id,
            key=PLAYGROUND_SQL_ACCESS_KEY,
            value="true" if payload.enabled else "false",
            context=build_sql_access_context(expires_at=expires_at_value),
        )
        db.add(preference)
    else:
        preference.value = "true" if payload.enabled else "false"
        preference.context = build_sql_access_context(expires_at=expires_at_value)

    is_active, _ = evaluate_sql_access(preference.value, preference.context)
    parsed_ctx = parse_sql_access_context(preference.context)
    _log_sql_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        enabled=payload.enabled,
        expires_at=parsed_ctx.get("expires_at"),
        action="grant_sql_full_access" if payload.enabled else "revoke_sql_full_access",
    )
    await db.commit()
    _invalidate_playground_sql_cache(user_id=user_id)
    return PlaygroundSqlAccessItem(
        user_id=user_id,
        enabled=payload.enabled,
        active=is_active,
        expires_at=parsed_ctx.get("expires_at"),
    )


@router.post("/playground-sql-access/revoke-all")
async def revoke_all_playground_sql_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(UserPreference).where(UserPreference.key == PLAYGROUND_SQL_ACCESS_KEY)
    )
    preferences = result.scalars().all()
    revoked_count = 0
    for pref in preferences:
        if str(pref.value).lower() == "true":
            pref.value = "false"
            pref.context = build_sql_access_context(expires_at=None)
            revoked_count += 1
    _log_sql_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        enabled=False,
        expires_at=None,
        action="revoke_sql_full_access_bulk",
    )
    await db.commit()
    _invalidate_playground_sql_cache(user_id=None)
    return {
        "status": "ok",
        "revoked_count": revoked_count,
        "message": "Permissão SQL completo revogada para usuários não-admin configurados.",
    }


@router.get("/playground-canary-access", response_model=list[PlaygroundCanaryAccessItem])
async def list_playground_canary_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlaygroundCanaryAccessItem]:
    result = await db.execute(
        select(UserPreference).where(UserPreference.key == PLAYGROUND_CANARY_ACCESS_KEY)
    )
    rows = result.scalars().all()
    return [
        PlaygroundCanaryAccessItem(
            user_id=str(row.user_id),
            enabled=str(row.value).strip().lower() == "true",
        )
        for row in rows
    ]


@router.put("/playground-canary-access/{user_id}", response_model=PlaygroundCanaryAccessItem)
async def update_playground_canary_access(
    user_id: str,
    payload: PlaygroundCanaryAccessUpdate,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaygroundCanaryAccessItem:
    try:
        target_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id inválido")

    pref_result = await db.execute(
        select(UserPreference).where(
            (UserPreference.user_id == target_user_id)
            & (UserPreference.key == PLAYGROUND_CANARY_ACCESS_KEY)
        )
    )
    preference = pref_result.scalar_one_or_none()
    if preference is None:
        preference = UserPreference(
            user_id=target_user_id,
            key=PLAYGROUND_CANARY_ACCESS_KEY,
            value="true" if payload.enabled else "false",
            context=None,
        )
        db.add(preference)
    else:
        preference.value = "true" if payload.enabled else "false"

    _log_canary_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        enabled=payload.enabled,
        action="grant_playground_canary_access" if payload.enabled else "revoke_playground_canary_access",
    )
    await db.commit()
    _invalidate_playground_canary_cache(user_id=user_id)
    return PlaygroundCanaryAccessItem(user_id=user_id, enabled=payload.enabled)


@router.post("/playground-canary-access/revoke-all")
async def revoke_all_playground_canary_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(UserPreference).where(UserPreference.key == PLAYGROUND_CANARY_ACCESS_KEY)
    )
    preferences = result.scalars().all()
    revoked_count = 0
    for pref in preferences:
        if str(pref.value).strip().lower() == "true":
            pref.value = "false"
            revoked_count += 1

    _log_canary_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        enabled=False,
        action="revoke_playground_canary_access_bulk",
    )
    await db.commit()
    _invalidate_playground_canary_cache(user_id=None)
    return {
        "status": "ok",
        "revoked_count": revoked_count,
        "message": "Acesso canário do Playground revogado para usuários configurados.",
    }


@router.get("/playground-access", response_model=list[PlaygroundAccessItem])
async def list_playground_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlaygroundAccessItem]:
    try:
        result = await db.execute(
            select(UserPreference).where(UserPreference.key == PLAYGROUND_ACCESS_KEY)
        )
        rows = result.scalars().all()
    except SQLAlchemyError:
        # Ambiente local sem migração de user_preferences
        return []
    return [
        PlaygroundAccessItem(
            user_id=str(row.user_id),
            enabled=str(row.value).strip().lower() == "true",
        )
        for row in rows
    ]


@router.put("/playground-access/{user_id}", response_model=PlaygroundAccessItem)
async def update_playground_access(
    user_id: str,
    payload: PlaygroundAccessUpdate,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaygroundAccessItem:
    try:
        target_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id inválido")

    try:
        pref_result = await db.execute(
            select(UserPreference).where(
                (UserPreference.user_id == target_user_id)
                & (UserPreference.key == PLAYGROUND_ACCESS_KEY)
            )
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Tabela de permissões indisponível: {e}")
    preference = pref_result.scalar_one_or_none()
    if preference is None:
        preference = UserPreference(
            user_id=target_user_id,
            key=PLAYGROUND_ACCESS_KEY,
            value="true" if payload.enabled else "false",
            context=None,
        )
        db.add(preference)
    else:
        preference.value = "true" if payload.enabled else "false"

    _log_playground_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        enabled=payload.enabled,
        action="grant_playground_access" if payload.enabled else "revoke_playground_access",
    )
    await db.commit()
    _invalidate_playground_access_cache(user_id=user_id)
    return PlaygroundAccessItem(user_id=user_id, enabled=payload.enabled)


@router.post("/playground-access/revoke-all")
async def revoke_all_playground_access(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        result = await db.execute(
            select(UserPreference).where(UserPreference.key == PLAYGROUND_ACCESS_KEY)
        )
        preferences = result.scalars().all()
    except SQLAlchemyError:
        return {
            "status": "ok",
            "revoked_count": 0,
            "message": "Tabela de permissões indisponível no ambiente local.",
        }
    revoked_count = 0
    for pref in preferences:
        if str(pref.value).strip().lower() == "true":
            pref.value = "false"
            revoked_count += 1

    _log_playground_access_change(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        enabled=False,
        action="revoke_playground_access_bulk",
    )
    await db.commit()
    _invalidate_playground_access_cache(user_id=None)
    return {
        "status": "ok",
        "revoked_count": revoked_count,
        "message": "Acesso ao Playground revogado para usuários configurados.",
    }


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
    from backend.app.config.settings import settings

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
    from backend.app.config.settings import settings

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
    from backend.app.config.settings import settings

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
