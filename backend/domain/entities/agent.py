"""
Entity: Agent

Define a entidade Agent que representa um agente especializado do sistema.

Uso:
    from backend.domain.entities import Agent, AgentType
    
    agent = Agent(
        id="sql-agent-001",
        name="SQLAgent",
        agent_type=AgentType.SQL,
        description="Agente especializado em queries SQL"
    )

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class AgentType(str, Enum):
    """Tipos de agentes disponíveis no sistema."""
    
    ORCHESTRATOR = "orchestrator"
    SQL = "sql"
    INSIGHT = "insight"
    FORECAST = "forecast"
    METADATA = "metadata"
    TENANT = "tenant"
    SECURITY = "security"
    MONITORING = "monitoring"


class AgentStatus(str, Enum):
    """Status possíveis de um agente."""
    
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class Agent:
    """
    Entidade que representa um agente especializado do sistema.
    
    Attributes:
        id: Identificador único do agente
        name: Nome do agente
        agent_type: Tipo do agente (SQL, Insight, etc.)
        description: Descrição das responsabilidades
        status: Status atual do agente
        capabilities: Lista de capacidades/ferramentas
        created_at: Data de criação
        updated_at: Data da última atualização
    
    Example:
        >>> agent = Agent(
        ...     name="SQLAgent",
        ...     agent_type=AgentType.SQL,
        ...     description="Executa queries SQL"
        ... )
        >>> agent.is_available()
        True
    """
    
    name: str
    agent_type: AgentType
    description: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Verifica se o agente está disponível para processar requisições."""
        return self.status in (AgentStatus.IDLE, AgentStatus.WAITING)
    
    def set_processing(self) -> None:
        """Marca o agente como processando."""
        self.status = AgentStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def set_idle(self) -> None:
        """Marca o agente como ocioso."""
        self.status = AgentStatus.IDLE
        self.updated_at = datetime.utcnow()
    
    def set_error(self) -> None:
        """Marca o agente como em erro."""
        self.status = AgentStatus.ERROR
        self.updated_at = datetime.utcnow()
    
    def add_capability(self, capability: str) -> None:
        """Adiciona uma capacidade ao agente."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.updated_at = datetime.utcnow()
    
    def has_capability(self, capability: str) -> bool:
        """Verifica se o agente possui determinada capacidade."""
        return capability in self.capabilities
    
    def __repr__(self) -> str:
        return f"Agent(name={self.name}, type={self.agent_type.value}, status={self.status.value})"
