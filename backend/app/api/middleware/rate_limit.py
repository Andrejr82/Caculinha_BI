"""
RateLimitMiddleware - Middleware de Rate Limiting

Controla o número de requisições por tenant/usuário.

Uso:
    app.add_middleware(RateLimitMiddleware)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
import time
from typing import Dict, Tuple
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


logger = structlog.get_logger(__name__)


# Rate limit em memória (em produção, usar Redis)
_RATE_LIMITS: Dict[str, list] = defaultdict(list)

# Configurações padrão
DEFAULT_REQUESTS_PER_HOUR = 1000
DEFAULT_WINDOW_SECONDS = 3600


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting por tenant.
    
    Limita requisições baseado no plano do tenant.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Rotas sem rate limit
        if request.url.path.startswith("/api/v2/health"):
            return await call_next(request)
        
        # Desabilitar em desenvolvimento
        if os.getenv("RATE_LIMIT_DISABLED", "false").lower() == "true":
            return await call_next(request)
        
        # Obter identificador (tenant + user)
        tenant_id = getattr(request.state, "tenant_id", "default")
        user_id = getattr(request.state, "user_id", "anonymous")
        key = f"{tenant_id}:{user_id}"
        
        # Obter limite do plano
        tenant_config = getattr(request.state, "tenant_config", {})
        limits = tenant_config.get("limits", {})
        max_requests = limits.get("max_requests_per_hour", DEFAULT_REQUESTS_PER_HOUR)
        
        # Verificar rate limit
        allowed, remaining, reset_at = self._check_rate_limit(
            key, max_requests, DEFAULT_WINDOW_SECONDS
        )
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                tenant_id=tenant_id,
                user_id=user_id,
                limit=max_requests,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": max_requests,
                    "remaining": 0,
                    "reset_at": reset_at,
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(int(reset_at - time.time())),
                }
            )
        
        # Adicionar headers de rate limit
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        
        return response
    
    def _check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Verifica se a requisição está dentro do limite.
        
        Returns:
            Tuple de (allowed, remaining, reset_at)
        """
        now = time.time()
        window_start = now - window_seconds
        reset_at = int(now + window_seconds)
        
        # Limpar requisições antigas
        _RATE_LIMITS[key] = [ts for ts in _RATE_LIMITS[key] if ts > window_start]
        
        # Verificar limite
        current_count = len(_RATE_LIMITS[key])
        remaining = max(0, max_requests - current_count - 1)
        
        if current_count >= max_requests:
            return False, 0, reset_at
        
        # Registrar requisição
        _RATE_LIMITS[key].append(now)
        
        return True, remaining, reset_at


def get_rate_limit_status(tenant_id: str, user_id: str) -> Dict:
    """
    Retorna o status atual de rate limit.
    
    Args:
        tenant_id: ID do tenant
        user_id: ID do usuário
    
    Returns:
        Status do rate limit
    """
    key = f"{tenant_id}:{user_id}"
    now = time.time()
    window_start = now - DEFAULT_WINDOW_SECONDS
    
    requests = [ts for ts in _RATE_LIMITS.get(key, []) if ts > window_start]
    
    return {
        "key": key,
        "requests_in_window": len(requests),
        "window_seconds": DEFAULT_WINDOW_SECONDS,
    }


def reset_rate_limit(tenant_id: str, user_id: str):
    """Reseta o rate limit para um usuário."""
    key = f"{tenant_id}:{user_id}"
    _RATE_LIMITS.pop(key, None)
