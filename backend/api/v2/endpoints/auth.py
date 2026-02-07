"""
Auth Endpoint

Endpoints de autenticação: login, logout, refresh token.

Uso:
    POST /api/v2/auth/login
    POST /api/v2/auth/refresh
    GET /api/v2/auth/me

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, EmailStr
import structlog

from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

from backend.api.middleware.auth import create_access_token, decode_token


logger = structlog.get_logger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class LoginRequest(BaseModel):
    """Requisição de login."""
    email: str = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")
    tenant_id: Optional[str] = Field(None, description="ID do tenant")


class LoginResponse(BaseModel):
    """Resposta de login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas
    user_id: str
    tenant_id: str
    role: str


class UserProfile(BaseModel):
    """Perfil do usuário."""
    user_id: str
    email: str
    tenant_id: str
    role: str
    name: Optional[str] = None
    created_at: Optional[str] = None


class RefreshRequest(BaseModel):
    """Requisição de refresh token."""
    refresh_token: str


# =============================================================================
# MOCK USERS (em produção, usar banco de dados)
# =============================================================================

MOCK_USERS = {
    "admin@lojas-cacula.com.br": {
        "user_id": "user-001",
        "password": "admin123",
        "tenant_id": "lojas-cacula",
        "role": "admin",
        "name": "Administrador",
    },
    "user@lojas-cacula.com.br": {
        "user_id": "user-002",
        "password": "user123",
        "tenant_id": "lojas-cacula",
        "role": "user",
        "name": "Usuário Padrão",
    },
    "test@test.com": {
        "user_id": "user-test",
        "password": "test123",
        "tenant_id": "test-tenant",
        "role": "user",
        "name": "Usuário Teste",
    },
}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Autentica usuário e retorna token JWT.
    
    Args:
        request: Credenciais de login
    
    Returns:
        Token de acesso e informações do usuário
    """
    # Buscar usuário
    user = MOCK_USERS.get(request.email)
    
    if not user or user["password"] != request.password:
        logger.warning("login_failed", email=request.email)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Gerar token
    token = create_access_token(
        user_id=user["user_id"],
        tenant_id=request.tenant_id or user["tenant_id"],
        role=user["role"],
    )
    
    logger.info(
        "login_success",
        user_id=user["user_id"],
        tenant_id=user["tenant_id"],
    )
    
    return LoginResponse(
        access_token=token,
        user_id=user["user_id"],
        tenant_id=user["tenant_id"],
        role=user["role"],
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user(request: Request):
    """
    Retorna o perfil do usuário autenticado.
    
    Requer token de autenticação no header Authorization.
    """
    # Extrair token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = auth_header[7:]
    
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        
        # Buscar dados do usuário
        for email, user in MOCK_USERS.items():
            if user["user_id"] == user_id:
                return UserProfile(
                    user_id=user_id,
                    email=email,
                    tenant_id=payload.get("tenant_id"),
                    role=payload.get("role"),
                    name=user.get("name"),
                    created_at=datetime.utcnow().isoformat(),
                )
        
        return UserProfile(
            user_id=user_id,
            email="unknown",
            tenant_id=payload.get("tenant_id"),
            role=payload.get("role"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest):
    """
    Atualiza o token de acesso.
    
    Args:
        request: Token de refresh
    
    Returns:
        Novo token de acesso
    """
    try:
        payload = decode_token(request.refresh_token)
        
        # Gerar novo token
        token = create_access_token(
            user_id=payload["user_id"],
            tenant_id=payload["tenant_id"],
            role=payload.get("role", "user"),
        )
        
        return LoginResponse(
            access_token=token,
            user_id=payload["user_id"],
            tenant_id=payload["tenant_id"],
            role=payload.get("role", "user"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(request: Request):
    """
    Invalida o token do usuário.
    
    Em uma implementação real, adicionar token a uma blacklist.
    """
    # TODO: Implementar blacklist de tokens
    return {"message": "Logout realizado com sucesso"}
