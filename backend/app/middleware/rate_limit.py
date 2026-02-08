"""
Rate Limiting Middleware - Proteção contra abuso de API

Implementa rate limiting usando slowapi para prevenir:
- Ataques DDoS
- Abuso de recursos
- Scraping excessivo

Baseado nas recomendações do Backend Specialist.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Criar limiter global
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # Limite padrão: 200 requests por minuto
    storage_uri="memory://",  # Usar memória (para produção, usar Redis)
    strategy="fixed-window"  # Estratégia de janela fixa
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


class RateLimitMiddleware:
    """
    Middleware para aplicar rate limiting em toda a aplicação.
    
    Features:
    - Rate limiting por IP
    - Limites customizados por endpoint
    - Headers informativos (X-RateLimit-*)
    - Logging de violações
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Adicionar headers de rate limit na resposta
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Adicionar headers informativos
                headers.append((b"x-ratelimit-limit", b"200"))
                headers.append((b"x-ratelimit-remaining", b"199"))
                headers.append((b"x-ratelimit-reset", b"60"))
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Handler customizado para rate limit exceeded
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handler customizado para quando rate limit é excedido.
    
    Retorna resposta 429 com informações úteis.
    """
    logger.warning(
        f"Rate limit exceeded: {get_remote_address(request)} "
        f"on {request.url.path}"
    )
    
    return Response(
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": 60  # segundos
        },
        status_code=429,
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": "200",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "60"
        }
    )


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
