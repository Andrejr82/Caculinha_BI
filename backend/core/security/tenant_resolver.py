"""
Tenant Resolver — Resolver de Multi-Tenancy

Autor: Security Auditor Agent
Data: 2026-02-07
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
import structlog

logger = structlog.get_logger(__name__)


class TenantResolver:
    """Resolve e valida tenant para multi-tenancy."""
    
    def __init__(self):
        # Cache de tenants (em produção, vem do banco)
        self._tenants: Dict[str, Dict[str, Any]] = {
            "default": {"name": "Default", "active": True, "plan": "free"},
            "cacula": {"name": "Lojas Caçula", "active": True, "plan": "enterprise"},
        }
    
    def resolve(self, request: Request) -> str:
        """Resolve tenant do request."""
        # Prioridade: 1. Header, 2. Subdomain, 3. JWT
        tenant_id = (
            request.headers.get("X-Tenant-ID") or
            self._extract_from_subdomain(request) or
            getattr(request.state, "tenant_id", "default")
        )
        
        if not self.validate(tenant_id):
            raise HTTPException(status_code=403, detail=f"Invalid tenant: {tenant_id}")
        
        return tenant_id
    
    def validate(self, tenant_id: str) -> bool:
        """Valida se tenant existe e está ativo."""
        tenant = self._tenants.get(tenant_id)
        return tenant is not None and tenant.get("active", False)
    
    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retorna configuração do tenant."""
        return self._tenants.get(tenant_id)
    
    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """Extrai tenant do subdomain."""
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) > 2:
            return parts[0]
        return None
    
    def register_tenant(self, tenant_id: str, config: Dict[str, Any]):
        """Registra novo tenant."""
        self._tenants[tenant_id] = config
        logger.info("tenant_registered", tenant_id=tenant_id)


# Singleton
_resolver: Optional[TenantResolver] = None


def get_tenant_resolver() -> TenantResolver:
    global _resolver
    if _resolver is None:
        _resolver = TenantResolver()
    return _resolver
