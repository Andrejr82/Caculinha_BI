"""
Compatibility exports for legacy middleware imports.

The active runtime middleware lives under ``backend.app.api.middleware``.
"""

from .rate_limit import (
    RateLimitMiddleware,
    limiter,
    get_limiter,
    get_rate_limit,
    limit_auth,
    limit_chat,
    limit_read,
    limit_write,
    limit_admin
)

__all__ = [
    "RateLimitMiddleware",
    "limiter",
    "get_limiter",
    "get_rate_limit",
    "limit_auth",
    "limit_chat",
    "limit_read",
    "limit_write",
    "limit_admin"
]
