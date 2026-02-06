"""
Auth Schemas
Pydantic schemas for Authentication
"""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""

    user_id: str
    username: str
    role: str
    allowed_segments: list[str] = Field(default_factory=list) # Novo Campo


class LoginRequest(BaseModel):
    """Login request schema"""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)  # Removida validação de 8 chars para permitir senhas de teste


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str
