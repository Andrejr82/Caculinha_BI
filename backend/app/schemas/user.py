"""
User Schemas
Pydantic schemas for User API
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user"""

    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="viewer", pattern="^(admin|user|viewer)$")
    allowed_segments: list[str] = Field(default_factory=list) # Novo Campo


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    role: str | None = Field(None, pattern="^(admin|user|viewer)$")
    is_active: bool | None = None
    allowed_segments: list[str] | None = Field(None) # Novo Campo
    password: str | None = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""

    id: uuid.UUID
    role: str
    is_active: bool
    allowed_segments: list[str] = Field(default_factory=list) # Novo Campo com default
    email: EmailStr | None = None
    last_login: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("allowed_segments", mode="before")
    @classmethod
    def normalize_allowed_segments(cls, value):
        import json

        if value is None:
            return []
        if isinstance(value, list):
            normalized = [str(item) for item in value if str(item).strip()]
            return normalized
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    normalized = [str(item) for item in parsed if str(item).strip()]
                    return normalized
            except (TypeError, json.JSONDecodeError):
                return []
        return []

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """
        Custom validation to handle allowed_segments conversion from JSON string.
        FIXED: Use segments_list property from User model if available (handles parsing automatically).
        """
        # If obj is a User model instance with segments_list property, use it
        if hasattr(obj, 'segments_list'):
            # Create a dict from the object attributes
            role = getattr(obj, 'role', 'user')
            fallback_segments = ["*"] if role == "admin" else []
            allowed_segments = obj.segments_list if obj.segments_list else fallback_segments
            obj_dict = {
                'id': obj.id,
                'username': obj.username,
                'email': getattr(obj, 'email', None),
                'role': role,
                'is_active': obj.is_active,
                'allowed_segments': allowed_segments,
                'last_login': getattr(obj, 'last_login', None),
                'created_at': getattr(obj, 'created_at', None),
                'updated_at': getattr(obj, 'updated_at', None)
            }
            return super().model_validate(obj_dict, **kwargs)

        # Fallback: If obj is dict or has allowed_segments as string
        if hasattr(obj, 'allowed_segments'):
            import json
            role = getattr(obj, 'role', 'user')
            fallback_segments = ["*"] if role == "admin" else []
            raw_segments = obj.allowed_segments
            if isinstance(raw_segments, str):
                try:
                    parsed = json.loads(raw_segments) if raw_segments else []
                except (json.JSONDecodeError, TypeError):
                    parsed = []
                obj.allowed_segments = parsed if parsed else fallback_segments
            elif raw_segments is None:
                obj.allowed_segments = fallback_segments
            elif isinstance(raw_segments, list) and not raw_segments:
                obj.allowed_segments = fallback_segments

        return super().model_validate(obj, **kwargs)


class UserInDB(UserResponse):
    """Schema for user in database (includes hashed password)"""

    hashed_password: str
