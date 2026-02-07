"""
Security Module — Exportação de Segurança

Autor: Security Auditor Agent
Data: 2026-02-07
"""

from backend.core.security.jwt_middleware import JWTMiddleware, create_token, get_current_user
from backend.core.security.tenant_resolver import TenantResolver, get_tenant_resolver
from backend.core.security.rbac import RBAC, get_rbac, require_permission, require_role


__all__ = [
    "JWTMiddleware",
    "create_token",
    "get_current_user",
    "TenantResolver",
    "get_tenant_resolver",
    "RBAC",
    "get_rbac",
    "require_permission",
    "require_role",
]
