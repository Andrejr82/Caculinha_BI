"""
MonitoringAgent - Agente Especializado em Observabilidade

Este agente é responsável por monitorar a saúde do sistema,
coletar métricas e reportar status dos serviços.

Uso:
    from backend.application.agents import MonitoringAgent
    
    monitoring_agent = MonitoringAgent(metrics=prometheus_adapter)
    response = await monitoring_agent.run(request)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import psutil

import structlog

from backend.application.agents.base_agent import BaseAgent
from backend.domain.ports.agent_port import (
    AgentRequest,
    AgentResponse,
    AgentRequestType,
)
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.metrics_port import MetricsPort


logger = structlog.get_logger(__name__)


class MonitoringAgent(BaseAgent):
    """
    Agente especializado em observabilidade e monitoramento.
    
    Responsabilidades:
    - Monitorar saúde dos serviços
    - Coletar e reportar métricas
    - Detectar problemas de performance
    - Gerar alertas
    """
    
    def __init__(
        self,
        llm: Optional[LLMPort] = None,
        metrics: Optional[MetricsPort] = None,
        agents: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(llm=llm, metrics=metrics)
        self._agents = agents or {}
    
    @property
    def name(self) -> str:
        return "MonitoringAgent"
    
    @property
    def description(self) -> str:
        return (
            "Agente especializado em monitoramento de saúde do sistema, "
            "coleta de métricas e detecção de problemas de performance."
        )
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "health_check",
            "metrics_collection",
            "performance_monitoring",
            "alerting",
            "system_status",
        ]
    
    async def can_handle(self, request: AgentRequest) -> bool:
        if request.request_type == AgentRequestType.MONITORING:
            return True
        keywords = ["status", "saúde", "health", "monitoramento", "métricas", "performance"]
        return any(kw in request.message.lower() for kw in keywords)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Coleta métricas do sistema."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
            }
        except Exception as e:
            logger.warning("system_metrics_error", error=str(e))
            return {}
    
    async def check_agents_health(self) -> Dict[str, bool]:
        """Verifica saúde dos agentes."""
        health = {}
        for name, agent in self._agents.items():
            try:
                health[name] = await agent.health_check()
            except Exception:
                health[name] = False
        return health
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        # Coletar métricas
        system_metrics = await self.get_system_metrics()
        agents_health = await self.check_agents_health()
        
        # Determinar status geral
        cpu_ok = system_metrics.get("cpu_percent", 100) < 80
        mem_ok = system_metrics.get("memory_percent", 100) < 85
        all_agents_ok = all(agents_health.values()) if agents_health else True
        
        overall_status = "🟢 Saudável" if (cpu_ok and mem_ok and all_agents_ok) else "🟡 Atenção"
        
        content = f"""## Status do Sistema

**Status Geral:** {overall_status}
**Timestamp:** {datetime.utcnow().isoformat()}

### Recursos do Sistema
| Recurso | Uso | Status |
|---------|-----|--------|
| CPU | {system_metrics.get('cpu_percent', 'N/A')}% | {"✅" if cpu_ok else "⚠️"} |
| Memória | {system_metrics.get('memory_percent', 'N/A')}% | {"✅" if mem_ok else "⚠️"} |
| Disco | {system_metrics.get('disk_percent', 'N/A')}% | ✅ |

### Saúde dos Agentes
"""
        if agents_health:
            for agent, healthy in agents_health.items():
                status = "✅ Online" if healthy else "❌ Offline"
                content += f"- **{agent}:** {status}\n"
        else:
            content += "- Nenhum agente registrado para monitoramento\n"
        
        return AgentResponse(
            content=content,
            success=True,
            data={
                "system_metrics": system_metrics,
                "agents_health": agents_health,
                "overall_healthy": cpu_ok and mem_ok and all_agents_ok,
            },
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "verificar_saude_sistema",
                "description": "Verifica a saúde geral do sistema",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "coletar_metricas",
                "description": "Coleta métricas de CPU, memória e disco",
                "parameters": {"type": "object", "properties": {}},
            },
        ]
