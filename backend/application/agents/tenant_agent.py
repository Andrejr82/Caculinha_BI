"""
TenantAgent - Agente Especializado em Multi-Tenancy

Este agente é responsável por gerenciar contexto de tenant,
isolamento de dados e configurações específicas por organização.

Uso:
    from backend.application.agents import TenantAgent
    
    tenant_agent = TenantAgent()
    response = await tenant_agent.run(request)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import List, Dict, Any, Optional

import structlog

from backend.application.agents.base_agent import BaseAgent
from backend.domain.ports.agent_port import AgentRequest, AgentResponse
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.metrics_port import MetricsPort
from backend.domain.entities.tenant import Tenant, TenantStatus, TenantPlan


logger = structlog.get_logger(__name__)


class TenantAgent(BaseAgent):
    """
    Agente especializado em gerenciamento de multi-tenancy.
    
    Responsabilidades:
    - Resolver contexto de tenant
    - Aplicar filtros de isolamento de dados
    - Gerenciar configurações por tenant
    - Validar permissões de acesso
    """
    
    def __init__(
        self,
        llm: Optional[LLMPort] = None,
        metrics: Optional[MetricsPort] = None,
    ):
        super().__init__(llm=llm, metrics=metrics)
        self._tenant_cache: Dict[str, Tenant] = {}
    
    @property
    def name(self) -> str:
        return "TenantAgent"
    
    @property
    def description(self) -> str:
        return (
            "Agente especializado em gerenciamento de multi-tenancy, "
            "isolamento de dados e configurações por organização."
        )
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "tenant_resolution",
            "data_isolation",
            "tenant_config",
            "access_validation",
        ]
    
    async def can_handle(self, request: AgentRequest) -> bool:
        keywords = ["tenant", "organização", "empresa", "configuração"]
        return any(kw in request.message.lower() for kw in keywords)
    
    async def resolve_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Resolve e retorna informações do tenant."""
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]
        
        # Mock tenant (em produção, buscaria do banco)
        tenant = Tenant(
            id=tenant_id,
            name="Lojas Caçula",
            slug="lojas-cacula",
            status=TenantStatus.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
        )
        self._tenant_cache[tenant_id] = tenant
        return tenant
    
    def get_data_filter(self, tenant_id: str) -> str:
        """Retorna filtro SQL para isolamento de dados."""
        return f"tenant_id = '{tenant_id}'"
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        tenant = await self.resolve_tenant(request.tenant_id)
        
        if not tenant:
            return AgentResponse(
                content="Tenant não encontrado.",
                success=False,
            )
        
        content = f"""## Informações do Tenant

| Propriedade | Valor |
|-------------|-------|
| **Nome** | {tenant.name} |
| **ID** | {tenant.id} |
| **Status** | {tenant.status.value} |
| **Plano** | {tenant.plan.value} |
| **Usuários Permitidos** | {tenant.allowed_users} |
"""
        
        return AgentResponse(
            content=content,
            success=True,
            data=tenant.to_dict(),
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "resolver_tenant",
                "description": "Resolve informações do tenant atual",
                "parameters": {"type": "object", "properties": {}},
            },
        ]
