"""
BaseAgent — Classe Base para Agentes

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AgentRequest:
    """Requisição para um agente."""
    content: str
    conversation_id: str
    tenant_id: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Resposta de um agente."""
    content: str
    agent_name: str
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """Classe base abstrata para todos os agentes."""
    
    def __init__(self, name: str, description: str = "", capabilities: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.id = f"agent-{uuid4().hex[:8]}"
    
    @abstractmethod
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        """Lógica principal de execução (implementar nas subclasses)."""
        pass
    
    async def run(self, request: AgentRequest) -> AgentResponse:
        """Executa o agente com logging e tratamento de erro."""
        logger.info("agent_start", agent=self.name, conversation_id=request.conversation_id)
        try:
            response = await self._execute(request)
            logger.info("agent_complete", agent=self.name, success=response.success)
            return response
        except Exception as e:
            logger.error("agent_error", agent=self.name, error=str(e))
            return AgentResponse(content="", agent_name=self.name, success=False, error=str(e))
    
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "description": self.description, "capabilities": self.capabilities}
