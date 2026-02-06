"""
User Preferences Endpoints
Handles user preferences and persistent memory
"""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.infrastructure.database.models import UserPreference, User

router = APIRouter(prefix="/preferences", tags=["Preferences"])


# Pydantic Models
class PreferenceCreate(BaseModel):
    """Request to create or update a preference"""
    key: str
    value: str
    context: str | None = None


class PreferenceResponse(BaseModel):
    """Preference response"""
    id: str
    key: str
    value: str
    context: str | None
    created_at: str
    updated_at: str


class PreferenceListResponse(BaseModel):
    """List of preferences"""
    preferences: dict[str, str]  # key: value mapping


@router.get("", response_model=PreferenceListResponse)
async def list_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all preferences for the current user.

    Returns a dictionary mapping preference keys to values.
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalars().all()

    return PreferenceListResponse(
        preferences={pref.key: pref.value for pref in preferences}
    )


@router.get("/{key}")
async def get_preference(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific preference by key.
    """
    result = await db.execute(
        select(UserPreference).where(
            and_(
                UserPreference.user_id == current_user.id,
                UserPreference.key == key
            )
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference '{key}' not found"
        )

    return PreferenceResponse(
        id=str(preference.id),
        key=preference.key,
        value=preference.value,
        context=preference.context,
        created_at=preference.created_at.isoformat(),
        updated_at=preference.updated_at.isoformat()
    )


@router.post("", response_model=PreferenceResponse)
async def set_preference(
    request: PreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create or update a preference.

    If the preference already exists, it will be updated.
    """
    # Check if preference exists
    result = await db.execute(
        select(UserPreference).where(
            and_(
                UserPreference.user_id == current_user.id,
                UserPreference.key == request.key
            )
        )
    )
    existing_pref = result.scalar_one_or_none()

    if existing_pref:
        # Update existing preference
        existing_pref.value = request.value
        if request.context is not None:
            existing_pref.context = request.context
        await db.commit()
        await db.refresh(existing_pref)
        preference = existing_pref
    else:
        # Create new preference
        preference = UserPreference(
            user_id=current_user.id,
            key=request.key,
            value=request.value,
            context=request.context
        )
        db.add(preference)
        await db.commit()
        await db.refresh(preference)

    return PreferenceResponse(
        id=str(preference.id),
        key=preference.key,
        value=preference.value,
        context=preference.context,
        created_at=preference.created_at.isoformat(),
        updated_at=preference.updated_at.isoformat()
    )


@router.put("/batch")
async def set_preferences_batch(
    preferences: dict[str, str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Set multiple preferences at once.

    Accepts a dictionary of key-value pairs.
    """
    updated_count = 0
    created_count = 0

    for key, value in preferences.items():
        # Check if preference exists
        result = await db.execute(
            select(UserPreference).where(
                and_(
                    UserPreference.user_id == current_user.id,
                    UserPreference.key == key
                )
            )
        )
        existing_pref = result.scalar_one_or_none()

        if existing_pref:
            existing_pref.value = value
            updated_count += 1
        else:
            new_pref = UserPreference(
                user_id=current_user.id,
                key=key,
                value=value
            )
            db.add(new_pref)
            created_count += 1

    await db.commit()

    return {
        "message": "Preferences updated successfully",
        "updated": updated_count,
        "created": created_count,
        "total": len(preferences)
    }


@router.delete("/{key}")
async def delete_preference(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a specific preference.
    """
    result = await db.execute(
        select(UserPreference).where(
            and_(
                UserPreference.user_id == current_user.id,
                UserPreference.key == key
            )
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference '{key}' not found"
        )

    await db.delete(preference)
    await db.commit()

    return {"message": f"Preference '{key}' deleted successfully"}


@router.get("/common/keys")
async def get_common_keys() -> Any:
    """
    Get list of common preference keys with descriptions.

    Useful for frontend to know what preferences are available.
    """
    return {
        "keys": [
            {
                "key": UserPreference.Keys.PREFERRED_CHART_TYPE,
                "description": "Tipo de gráfico preferido",
                "options": ["bar", "line", "pie", "scatter"],
                "default": "bar"
            },
            {
                "key": UserPreference.Keys.PREFERRED_DATA_FORMAT,
                "description": "Formato de dados preferido",
                "options": ["table", "chart", "both"],
                "default": "both"
            },
            {
                "key": UserPreference.Keys.LANGUAGE,
                "description": "Idioma",
                "options": ["pt-BR", "en-US"],
                "default": "pt-BR"
            },
            {
                "key": UserPreference.Keys.THEME,
                "description": "Tema",
                "options": ["light", "dark"],
                "default": "light"
            },
            {
                "key": UserPreference.Keys.COMPANY_NAME,
                "description": "Nome da empresa",
                "type": "text"
            },
            {
                "key": UserPreference.Keys.BUSINESS_SEGMENT,
                "description": "Segmento de negócio",
                "type": "text"
            },
            {
                "key": UserPreference.Keys.ANALYSIS_FOCUS,
                "description": "Foco principal de análise",
                "options": ["sales", "inventory", "finance"],
                "default": "sales"
            },
            {
                "key": UserPreference.Keys.NOTIFICATION_ENABLED,
                "description": "Notificações habilitadas",
                "options": ["true", "false"],
                "default": "true"
            }
        ]
    }
