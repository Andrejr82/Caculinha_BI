"""
Port: AgentPort

Interface abstrata que todos os agentes devem implementar.
Esta é a interface base para o sistema multi-agente.

Uso:
    from backend.domain.ports import AgentPort
    
    class SQLAgent(AgentPort):
        async def run(self, request):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentRequestType(str, Enum):
    """Tipos de requisição para agentes."""
    
    QUERY = "query"
    INSIGHT = "insight"
    FORECAST = "forecast"
    METADATA = "metadata"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class AgentRequest:
    """
    Requisição padronizada para agentes.
    
    Attributes:
        message: Mensagem/comando do usuário
        conversation_id: ID da conversa
        tenant_id: ID do tenant (multi-tenancy)
        user_id: ID do usuário
        context: Contexto adicional
        request_type: Tipo da requisição
        metadata: Metadados
    """
    
    message: str
    conversation_id: str
    tenant_id: str
    user_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    request_type: AgentRequestType = AgentRequestType.QUERY
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResponse:
    """
    Resposta padronizada de agentes.
    
    Attributes:
        content: Conteúdo da resposta
        success: Se a execução foi bem sucedida
        agent_name: Nome do agente que respondeu
        execution_time_ms: Tempo de execução em ms
        tool_calls: Ferramentas utilizadas
        insights: Insights gerados
        data: Dados estruturados (opcional)
        error: Mensagem de erro (se houver)
    """
    
    content: str
    success: bool = True
    agent_name: str = ""
    execution_time_ms: float = 0.0
    tool_calls: List[str] = field(default_factory=list)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a resposta para dicionário."""
        return {
            "content": self.content,
            "success": self.success,
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms,
            "tool_calls": self.tool_calls,
            "insights": self.insights,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentPort(ABC):
    """
    Interface abstrata que todos os agentes devem implementar.
    
    Esta é a porta base para o sistema multi-agente.
    Todos os agentes (SQLAgent, InsightAgent, etc.) devem herdar desta interface.
    
    Example:
        >>> class SQLAgent(AgentPort):
        ...     @property
        ...     def name(self) -> str:
        ...         return "SQLAgent"
        ...     
        ...     async def run(self, request: AgentRequest) -> AgentResponse:
        ...         # Executar query SQL
        ...         pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna o nome do agente."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Retorna a descrição do agente."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Retorna a lista de capacidades do agente."""
        pass
    
    @abstractmethod
    async def run(self, request: AgentRequest) -> AgentResponse:
        """
        Executa o agente com a requisição fornecida.
        
        Args:
            request: Requisição do agente
        
        Returns:
            AgentResponse com o resultado
        """
        pass
    
    @abstractmethod
    async def can_handle(self, request: AgentRequest) -> bool:
        """
        Verifica se o agente pode lidar com a requisição.
        
        Args:
            request: Requisição a verificar
        
        Returns:
            True se pode lidar
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica se o agente está saudável.
        
        Returns:
            True se saudável
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de ferramentas disponíveis.
        
        Returns:
            Lista de definições de ferramentas
        """
        pass
