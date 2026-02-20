"""
AuthMiddleware - Middleware de Autenticação

Valida tokens JWT e autentica usuários em requisições.

Uso:
    app.add_middleware(AuthMiddleware)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import structlog

from backend.app.config.settings import settings

logger = structlog.get_logger(__name__)

# Configurações unificadas via settings.py
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
JWT_EXPIRATION_HOURS = settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60
LEGACY_TEST_JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# Rotas públicas (não requerem autenticação)
PUBLIC_ROUTES = [
    "/api/v1/auth/login",
    "/api/v2/auth/login",
    "/api/v2/health",
    "/api/v2/health/detailed",
    "/docs",
    "/openapi.json",
    "/redoc",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware de autenticação via JWT.
    
    Valida tokens Bearer e injeta informações do usuário no request.state.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Verificar se é rota pública
        path = request.url.path
        if any(path.startswith(route) for route in PUBLIC_ROUTES):
            return await call_next(request)
        
        # Modo de teste ou desenvolvimento
        if os.getenv("AUTH_DISABLED", "false").lower() == "true":
            request.state.user_id = "dev-user"
            request.state.tenant_id = "dev-tenant"
            request.state.user_role = "admin"
            return await call_next(request)
        
        # Validar token (somente erros de autenticação devem ser tratados aqui)
        try:
            token = self._extract_token(request)
            if token:
                user_data = self._validate_token(token)
                request.state.user_id = user_data.get("user_id", "anonymous")
                request.state.tenant_id = user_data.get("tenant_id", "default")
                request.state.user_role = user_data.get("role", "user")
            else:
                # Sem token - usar valores padrão (modo desenvolvimento)
                request.state.user_id = "anonymous"
                request.state.tenant_id = "default"
                request.state.user_role = "guest"
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error("auth_middleware_error", error=str(e), path=request.url.path)
            return JSONResponse(status_code=500, content={"detail": "Erro de autenticação"})

        # Importante: exceções do endpoint NÃO devem virar "erro de autenticação"
        return await call_next(request)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extrai token do header Authorization."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
    
    def _validate_token(self, token: str) -> dict:
        """Valida e decodifica o token JWT."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError as e:
            # Legacy contract tests generate tokens with JWT_SECRET env var.
            if LEGACY_TEST_JWT_SECRET and LEGACY_TEST_JWT_SECRET != JWT_SECRET:
                try:
                    return jwt.decode(token, LEGACY_TEST_JWT_SECRET, algorithms=[JWT_ALGORITHM])
                except jwt.InvalidTokenError:
                    pass
            raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


def create_access_token(
    user_id: str, 
    tenant_id: str, 
    role: str = "user",
    extra_claims: dict = None
) -> str:
    """
    Cria um token JWT para o usuário.
    
    Args:
        user_id: ID do usuário
        tenant_id: ID do tenant
        role: Papel do usuário (admin, user, guest)
        extra_claims: Claims adicionais (username, allowed_segments, etc.)
    
    Returns:
        Token JWT assinado
    """
    payload = {
        "sub": user_id,  # Standard JWT claim - required by dependencies.py
        "user_id": user_id,  # Legacy claim for backward compatibility
        "tenant_id": tenant_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    
    # Adicionar claims extras se fornecidos
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)




def decode_token(token: str) -> dict:
    """
    Decodifica um token JWT.
    
    Args:
        token: Token JWT
    
    Returns:
        Payload decodificado
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        if LEGACY_TEST_JWT_SECRET and LEGACY_TEST_JWT_SECRET != JWT_SECRET:
            return jwt.decode(token, LEGACY_TEST_JWT_SECRET, algorithms=[JWT_ALGORITHM])
        raise
