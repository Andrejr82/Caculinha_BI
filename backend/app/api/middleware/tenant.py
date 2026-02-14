"""
TenantMiddleware - Middleware de Multi-Tenancy

Resolve e injeta contexto de tenant em todas as requisições.

Uso:
    app.add_middleware(TenantMiddleware)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from typing import Optional, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


logger = structlog.get_logger(__name__)


# Cache de tenants em memória (em produção, usar Redis)
_TENANT_CACHE: Dict[str, Dict[str, Any]] = {}

# Configurações padrão por plano
TENANT_PLANS = {
    "free": {
        "max_requests_per_hour": 100,
        "max_tokens_per_request": 4096,
        "max_conversations": 10,
        "features": ["chat", "basic_insights"],
    },
    "pro": {
        "max_requests_per_hour": 1000,
        "max_tokens_per_request": 8192,
        "max_conversations": 100,
        "features": ["chat", "insights", "forecasts", "sql"],
    },
    "enterprise": {
        "max_requests_per_hour": 10000,
        "max_tokens_per_request": 32768,
        "max_conversations": -1,  # Ilimitado
        "features": ["chat", "insights", "forecasts", "sql", "custom_agents", "api"],
    },
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware de multi-tenancy.
    
    Resolve tenant_id e injeta configurações no request.state.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Resolver tenant
        tenant_id = self._resolve_tenant_id(request)
        tenant_config = self._get_tenant_config(tenant_id)
        
        # Injetar no request
        request.state.tenant_id = tenant_id
        request.state.tenant_config = tenant_config
        request.state.tenant_plan = tenant_config.get("plan", "free")
        
        # Log de contexto
        logger.bind(
            tenant_id=tenant_id,
            plan=tenant_config.get("plan"),
        )
        
        return await call_next(request)
    
    def _resolve_tenant_id(self, request: Request) -> str:
        """Resolve tenant_id de múltiplas fontes."""
        # 1. Header explícito
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # 2. Do state (injetado pelo AuthMiddleware)
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id
        
        # 3. Subdomínio (para SaaS)
        host = request.headers.get("Host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "localhost"]:
                return subdomain
        
        # 4. Default
        return os.getenv("DEFAULT_TENANT_ID", "default")
    
    def _get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Obtém configurações do tenant."""
        # Verificar cache
        if tenant_id in _TENANT_CACHE:
            return _TENANT_CACHE[tenant_id]
        
        # Mock de configuração (em produção, buscar do banco)
        config = {
            "id": tenant_id,
            "name": tenant_id.replace("-", " ").title(),
            "plan": "enterprise" if tenant_id == "lojas-cacula" else "pro",
            "status": "active",
            "settings": {
                "default_language": "pt-BR",
                "timezone": "America/Sao_Paulo",
            },
        }
        
        # Adicionar limites do plano
        plan = config["plan"]
        config["limits"] = TENANT_PLANS.get(plan, TENANT_PLANS["free"])
        
        # Cachear
        _TENANT_CACHE[tenant_id] = config
        
        return config


def get_tenant_limits(tenant_id: str) -> Dict[str, Any]:
    """
    Retorna os limites do tenant.
    
    Args:
        tenant_id: ID do tenant
    
    Returns:
        Dicionário com limites
    """
    config = _TENANT_CACHE.get(tenant_id, {})
    plan = config.get("plan", "free")
    return TENANT_PLANS.get(plan, TENANT_PLANS["free"])


def clear_tenant_cache(tenant_id: Optional[str] = None):
    """
    Limpa o cache de tenants.
    
    Args:
        tenant_id: ID específico ou None para limpar tudo
    """
    global _TENANT_CACHE
    if tenant_id:
        _TENANT_CACHE.pop(tenant_id, None)
    else:
        _TENANT_CACHE = {}
