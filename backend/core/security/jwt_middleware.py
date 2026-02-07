"""
JWT Middleware — Autenticação e Multi-Tenancy

Autor: Security Auditor Agent
Data: 2026-02-07
"""

from typing import Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import structlog

logger = structlog.get_logger(__name__)

# Configuração (em produção, vem do .env)
JWT_SECRET = "caculinha-bi-secret-key-2026"
JWT_ALGORITHM = "HS256"


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticação JWT com extração de tenant."""
    
    EXCLUDED_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health", "/api/v1/auth/login"}
    
    async def dispatch(self, request: Request, call_next):
        # Pula paths excluídos
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Extrai e valida token
        try:
            token = self._extract_token(request)
            if token:
                payload = self._verify_token(token)
                request.state.tenant_id = payload.get("tenant_id", "default")
                request.state.user_id = payload.get("sub", "anonymous")
                request.state.roles = payload.get("roles", [])
        except HTTPException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        
        return await call_next(request)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def _verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


def create_token(user_id: str, tenant_id: str, roles: list = None) -> str:
    """Cria token JWT."""
    import datetime
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles or ["user"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(request: Request) -> Tuple[str, str, list]:
    """Extrai user_id, tenant_id e roles do request."""
    return (
        getattr(request.state, "user_id", "anonymous"),
        getattr(request.state, "tenant_id", "default"),
        getattr(request.state, "roles", []),
    )
