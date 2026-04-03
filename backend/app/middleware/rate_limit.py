"""
Compatibility layer for legacy rate-limit imports.

The active runtime middleware lives in ``backend.app.api.middleware.rate_limit``.
This module only keeps the decorator-based ``slowapi`` helpers used by older
tests and compatibility imports.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.app.api.middleware.rate_limit import RateLimitMiddleware

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri="memory://",
    strategy="fixed-window",
)


def get_limiter() -> Limiter:
    """
    Retorna instância do limiter para uso em endpoints.
    
    Usage:
        from backend.app.middleware.rate_limit import get_limiter, limiter
        
        @app.post("/api/v1/chat")
        @limiter.limit("100/minute")
        async def chat_endpoint(request: Request):
            ...
    """
    return limiter


# Limites customizados por tipo de endpoint
RATE_LIMITS = {
    # Endpoints de autenticação (mais restritivos)
    "auth": "10/minute",
    
    # Endpoints de chat/IA (moderado)
    "chat": "100/minute",
    "tools": "200/minute",
    
    # Endpoints de leitura (mais permissivo)
    "read": "500/minute",
    
    # Endpoints de escrita (moderado)
    "write": "100/minute",
    
    # Endpoints administrativos (restritivo)
    "admin": "50/minute",
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Retorna o rate limit apropriado para o tipo de endpoint.
    
    Args:
        endpoint_type: Tipo do endpoint (auth, chat, read, write, admin)
        
    Returns:
        String de rate limit (ex: "100/minute")
    """
    return RATE_LIMITS.get(endpoint_type, "200/minute")


# Decorators prontos para uso
def limit_auth(func):
    """Decorator para endpoints de autenticação (10/min)"""
    return limiter.limit(RATE_LIMITS["auth"])(func)


def limit_chat(func):
    """Decorator para endpoints de chat (100/min)"""
    return limiter.limit(RATE_LIMITS["chat"])(func)


def limit_read(func):
    """Decorator para endpoints de leitura (500/min)"""
    return limiter.limit(RATE_LIMITS["read"])(func)


def limit_write(func):
    """Decorator para endpoints de escrita (100/min)"""
    return limiter.limit(RATE_LIMITS["write"])(func)


def limit_admin(func):
    """Decorator para endpoints admin (50/min)"""
    return limiter.limit(RATE_LIMITS["admin"])(func)
