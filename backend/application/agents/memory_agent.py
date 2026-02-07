"""
MemoryAgent — Agente de Memória Conversacional

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List, Optional
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.ports.memory_repository_port import IMemoryRepository
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message

logger = structlog.get_logger(__name__)


class MemoryAgent(BaseAgent):
    """Agente responsável por gerenciar memória conversacional."""
    
    def __init__(self, memory_repository: IMemoryRepository):
        super().__init__(
            name="MemoryAgent",
            description="Gerencia memória conversacional",
            capabilities=["load_memory", "save_memory", "create_conversation"]
        )
        self.memory = memory_repository
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        # Carrega contexto da conversa
        messages = await self.load_memory(request.conversation_id)
        return AgentResponse(
            content=f"Memória carregada: {len(messages)} mensagens",
            agent_name=self.name,
            metadata={"message_count": len(messages)}
        )
    
    async def create_conversation(self, tenant_id: str, user_id: str, title: Optional[str] = None) -> Conversation:
        """Cria nova conversa."""
        conv = Conversation(tenant_id=tenant_id, user_id=user_id, title=title)
        await self.memory.save_conversation(conv)
        logger.info("conversation_created", conversation_id=conv.id)
        return conv
    
    async def load_memory(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """Carrega mensagens recentes."""
        return await self.memory.get_recent_messages(conversation_id, limit)
    
    async def save_message(self, message: Message) -> str:
        """Salva uma mensagem."""
        return await self.memory.add_message(message)
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Recupera conversa."""
        return await self.memory.get_conversation(conversation_id)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta conversa."""
        return await self.memory.delete_conversation(conversation_id)
