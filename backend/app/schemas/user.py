"""
User Schemas
Pydantic schemas for User API
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """
        Custom validation to handle allowed_segments conversion from JSON string.
        FIXED: Use segments_list property from User model if available (handles parsing automatically).
        """
        # If obj is a User model instance with segments_list property, use it
        if hasattr(obj, 'segments_list'):
            # Create a dict from the object attributes
            obj_dict = {
                'id': obj.id,
                'username': obj.username,
                'email': obj.email,
                'role': obj.role,
                'is_active': obj.is_active,
                'allowed_segments': obj.segments_list,  # [OK] Use parsed property
                'last_login': obj.last_login,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return super().model_validate(obj_dict, **kwargs)

        # Fallback: If obj is dict or has allowed_segments as string
        if hasattr(obj, 'allowed_segments') and isinstance(obj.allowed_segments, str):
            import json
            try:
                obj.allowed_segments = json.loads(obj.allowed_segments) if obj.allowed_segments else []
            except (json.JSONDecodeError, TypeError):
                obj.allowed_segments = []

        return super().model_validate(obj, **kwargs)


class UserInDB(UserResponse):
    """Schema for user in database (includes hashed password)"""

    hashed_password: str
