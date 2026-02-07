"""
RBAC — Role-Based Access Control

Autor: Security Auditor Agent
Data: 2026-02-07
"""

from typing import List, Set
from functools import wraps
from fastapi import Request, HTTPException
import structlog

logger = structlog.get_logger(__name__)


# Definição de roles e permissões
ROLES = {
    "admin": {"read", "write", "delete", "manage_users", "manage_tenants", "view_analytics"},
    "manager": {"read", "write", "view_analytics"},
    "analyst": {"read", "view_analytics"},
    "user": {"read"},
}


class RBAC:
    """Role-Based Access Control."""
    
    def __init__(self):
        self.roles = ROLES.copy()
    
    def get_permissions(self, roles: List[str]) -> Set[str]:
        """Retorna conjunto de permissões para as roles."""
        permissions = set()
        for role in roles:
            if role in self.roles:
                permissions.update(self.roles[role])
        return permissions
    
    def has_permission(self, roles: List[str], permission: str) -> bool:
        """Verifica se roles têm permissão."""
        return permission in self.get_permissions(roles)
    
    def check_permission(self, request: Request, permission: str):
        """Verifica permissão e lança exceção se não tiver."""
        roles = getattr(request.state, "roles", [])
        if not self.has_permission(roles, permission):
            logger.warning("permission_denied", permission=permission, roles=roles)
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )
    
    def add_role(self, role: str, permissions: Set[str]):
        """Adiciona nova role."""
        self.roles[role] = permissions


# Singleton
_rbac: RBAC = RBAC()


def get_rbac() -> RBAC:
    return _rbac


def require_permission(permission: str):
    """Decorator para requerer permissão."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            if request:
                get_rbac().check_permission(request, permission)
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """Decorator para requerer role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            if request:
                roles = getattr(request.state, "roles", [])
                if role not in roles:
                    raise HTTPException(status_code=403, detail=f"Role required: {role}")
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
