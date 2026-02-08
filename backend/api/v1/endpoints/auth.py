"""
Auth Endpoint (API V1)

Endpoints de autenticação: login, logout, refresh token.
Reexporta lógica do V2 para manter compatibilidade com frontend.

Uso:
    POST /api/v1/auth/login
    POST /api/v1/auth/refresh
    GET /api/v1/auth/me

Autor: Backend Specialist Agent
Data: 2026-02-08
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import structlog

from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

from backend.api.middleware.auth import create_access_token, decode_token


logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# =============================================================================
# SCHEMAS
# =============================================================================

class LoginRequest(BaseModel):
    """Requisição de login."""
    username: str = Field(..., description="Username ou Email do usuário")
    password: str = Field(..., description="Senha do usuário")
    tenant_id: Optional[str] = Field(None, description="ID do tenant")


class LoginResponse(BaseModel):
    """Resposta de login."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None


class UserProfile(BaseModel):
    """Perfil do usuário."""
    user_id: str
    email: str
    username: str
    tenant_id: str
    role: str
    allowed_segments: list[str] = []
    name: Optional[str] = None
    created_at: Optional[str] = None


class RefreshRequest(BaseModel):
    """Requisição de refresh token."""
    refresh_token: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Autentica usuário via AuthService (Supabase > Parquet > SQL).
    """
    from backend.app.core.auth_service import auth_service
    
    # Autenticar usando o serviço centralizado
    user = await auth_service.authenticate_user(request.username, request.password)
    
    if not user:
        logger.warning("login_failed", username=request.username)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Adaptação para campos retornados pelo AuthService
    user_id = user.get("id") or user.get("user_id")
    tenant_id = request.tenant_id or user.get("tenant_id", "default")
    role = user.get("role", "user")
    username = user.get("username", request.username)
    allowed_segments = user.get("allowed_segments", [])
    
    # Gerar token local (Session Token)
    token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        extra_claims={
            "username": username,
            "allowed_segments": allowed_segments
        }
    )
    
    logger.info(
        "login_success",
        user_id=user_id,
        tenant_id=tenant_id,
        provider="auth_service"
    )
    
    return LoginResponse(
        access_token=token,
        refresh_token=token,  # Simplificado: mesmo token para refresh
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user(request: Request):
    """
    Retorna o perfil do usuário autenticado a partir do token.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = auth_header[7:]
    
    try:
        payload = decode_token(token)
        return UserProfile(
            user_id=payload.get("user_id", ""),
            email=payload.get("sub", "unknown"),
            username=payload.get("username", "user"),
            tenant_id=payload.get("tenant_id", "default"),
            role=payload.get("role", "user"),
            allowed_segments=payload.get("allowed_segments", []),
            name=payload.get("name", "Usuário"),
            created_at=datetime.fromtimestamp(payload.get("iat", 0)).isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest):
    """
    Atualiza o token de acesso.
    """
    try:
        payload = decode_token(request.refresh_token)
        
        # Gerar novo token
        token = create_access_token(
            user_id=payload["user_id"],
            tenant_id=payload.get("tenant_id", "default"),
            role=payload.get("role", "user"),
            extra_claims={
                "username": payload.get("username", "user"),
                "allowed_segments": payload.get("allowed_segments", [])
            }
        )
        
        return LoginResponse(
            access_token=token,
            refresh_token=token,
            user_id=payload["user_id"],
            tenant_id=payload.get("tenant_id", "default"),
            role=payload.get("role", "user"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(request: Request):
    """
    Invalida o token do usuário.
    """
    return {"message": "Logout realizado com sucesso"}
