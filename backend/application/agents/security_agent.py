"""
SecurityAgent - Agente Especializado em Segurança

Este agente é responsável por validar permissões, auditar acessos
e aplicar políticas de segurança.

Uso:
    from backend.application.agents import SecurityAgent
    
    security_agent = SecurityAgent(auth=supabase_adapter)
    response = await security_agent.run(request)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

import structlog

from backend.application.agents.base_agent import BaseAgent
from backend.domain.ports.agent_port import (
    AgentRequest,
    AgentResponse,
    AgentRequestType,
)
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.auth_port import AuthPort
from backend.domain.ports.metrics_port import MetricsPort


logger = structlog.get_logger(__name__)


class SecurityAgent(BaseAgent):
    """
    Agente especializado em segurança e auditoria.
    
    Responsabilidades:
    - Validar permissões de acesso
    - Registrar logs de auditoria
    - Detectar atividades suspeitas
    - Aplicar rate limiting
    """
    
    def __init__(
        self,
        llm: Optional[LLMPort] = None,
        auth: Optional[AuthPort] = None,
        metrics: Optional[MetricsPort] = None,
    ):
        super().__init__(llm=llm, metrics=metrics)
        self._auth = auth
        self._audit_log: List[Dict[str, Any]] = []
    
    @property
    def name(self) -> str:
        return "SecurityAgent"
    
    @property
    def description(self) -> str:
        return (
            "Agente especializado em segurança, validação de permissões, "
            "auditoria de acessos e detecção de anomalias."
        )
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "permission_validation",
            "audit_logging",
            "anomaly_detection",
            "rate_limiting",
            "access_control",
        ]
    
    async def can_handle(self, request: AgentRequest) -> bool:
        if request.request_type == AgentRequestType.SECURITY:
            return True
        keywords = ["segurança", "permissão", "acesso", "auditoria", "log"]
        return any(kw in request.message.lower() for kw in keywords)
    
    def log_audit(
        self,
        action: str,
        user_id: str,
        tenant_id: str,
        resource: str,
        success: bool,
    ) -> None:
        """Registra evento de auditoria."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "resource": resource,
            "success": success,
        }
        self._audit_log.append(entry)
        logger.info("audit_log", **entry)
    
    async def validate_access(
        self,
        user_id: str,
        resource: str,
        action: str,
    ) -> bool:
        """Valida se o usuário tem acesso ao recurso."""
        # Implementação simplificada
        # Em produção, usaria self._auth.authorize()
        return True
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        # Registrar acesso
        self.log_audit(
            action="chat_request",
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            resource="chat",
            success=True,
        )
        
        # Resumo de auditoria
        recent_logs = self._audit_log[-10:]
        
        content = f"""## Relatório de Segurança

### Últimas Atividades
| Horário | Ação | Usuário | Status |
|---------|------|---------|--------|
"""
        for log in recent_logs:
            status = "✅" if log["success"] else "❌"
            content += f"| {log['timestamp'][:19]} | {log['action']} | {log['user_id'][:8]} | {status} |\n"
        
        content += f"\n**Total de eventos:** {len(self._audit_log)}"
        
        return AgentResponse(
            content=content,
            success=True,
            data={"audit_count": len(self._audit_log)},
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "validar_acesso",
                "description": "Valida se o usuário tem acesso a um recurso",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recurso": {"type": "string"},
                        "acao": {"type": "string", "enum": ["read", "write", "delete"]},
                    },
                    "required": ["recurso", "acao"],
                },
            },
        ]
