"""
Entity: Tenant

Define a entidade Tenant para suporte a multi-tenancy.

Uso:
    from backend.domain.entities import Tenant
    
    tenant = Tenant(
        name="Lojas Caçula",
        slug="lojas-cacula"
    )

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4


class TenantStatus(str, Enum):
    """Status possíveis de um tenant."""
    
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"


class TenantPlan(str, Enum):
    """Planos disponíveis para tenants."""
    
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class Tenant:
    """
    Entidade que representa um tenant (organização) no sistema multi-tenant.
    
    Attributes:
        id: Identificador único do tenant
        name: Nome do tenant/organização
        slug: Identificador amigável para URLs
        status: Status do tenant
        plan: Plano de assinatura
        settings: Configurações específicas do tenant
        created_at: Data de criação
        updated_at: Data da última atualização
    
    Example:
        >>> tenant = Tenant(name="Lojas Caçula", slug="lojas-cacula")
        >>> tenant.is_active
        True
    """
    
    name: str
    slug: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    settings: Dict[str, Any] = field(default_factory=dict)
    allowed_users: int = 5
    allowed_agents: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Verifica se o tenant está ativo."""
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL)
    
    @property
    def is_enterprise(self) -> bool:
        """Verifica se o tenant é enterprise."""
        return self.plan == TenantPlan.ENTERPRISE
    
    def can_use_agent(self, agent_type: str) -> bool:
        """Verifica se o tenant pode usar determinado agente."""
        if self.is_enterprise:
            return True
        return agent_type in self.allowed_agents
    
    def set_setting(self, key: str, value: Any) -> None:
        """Define uma configuração do tenant."""
        self.settings[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtém uma configuração do tenant."""
        return self.settings.get(key, default)
    
    def add_data_source(self, source: str) -> None:
        """Adiciona uma fonte de dados ao tenant."""
        if source not in self.data_sources:
            self.data_sources.append(source)
            self.updated_at = datetime.utcnow()
    
    def suspend(self) -> None:
        """Suspende o tenant."""
        self.status = TenantStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Ativa o tenant."""
        self.status = TenantStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o tenant para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "plan": self.plan.value,
            "allowed_users": self.allowed_users,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"Tenant(name='{self.name}', status={self.status.value}, plan={self.plan.value})"
