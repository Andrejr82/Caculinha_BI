"""
Middleware - Inicialização

Este módulo contém os middlewares da aplicação.

Uso:
    from backend.api.middleware import AuthMiddleware, TenantMiddleware

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from .auth import AuthMiddleware
from .tenant import TenantMiddleware
from .rate_limit import RateLimitMiddleware

__all__ = ["AuthMiddleware", "TenantMiddleware", "RateLimitMiddleware"]
