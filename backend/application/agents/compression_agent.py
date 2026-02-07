"""
CompressionAgent — Agente de Compressão de Contexto

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.ports.compression_port import ICompressionPort, CompressedContext
from backend.domain.entities.message import Message

logger = structlog.get_logger(__name__)


class CompressionAgent(BaseAgent):
    """Agente responsável por compressão de contexto."""
    
    def __init__(self, compression_port: ICompressionPort):
        super().__init__(
            name="CompressionAgent",
            description="Comprime contexto longo",
            capabilities=["compress", "summarize", "extract_key_points"]
        )
        self.compressor = compression_port
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            content="Compression agent ready",
            agent_name=self.name
        )
    
    async def compress(
        self, messages: List[Message], max_tokens: int = 2000, preserve_recent: int = 3
    ) -> CompressedContext:
        """Comprime lista de mensagens."""
        return await self.compressor.compress_messages(messages, max_tokens, preserve_recent)
    
    async def summarize(self, messages: List[Message], focus: str = None) -> str:
        """Gera sumário de conversa."""
        return await self.compressor.summarize_conversation(messages, focus)
    
    async def should_compress(self, messages: List[Message], threshold: int = 4000) -> bool:
        """Verifica se compressão é necessária."""
        return await self.compressor.should_compress(messages, threshold)
    
    async def extract_key_points(self, messages: List[Message], max_points: int = 5) -> List[str]:
        """Extrai pontos-chave."""
        return await self.compressor.extract_key_points(messages, max_points)
