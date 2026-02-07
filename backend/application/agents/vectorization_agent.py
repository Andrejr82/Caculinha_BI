"""
VectorizationAgent — Agente de Vetorização

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List, Optional
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.entities.embedding import Embedding

logger = structlog.get_logger(__name__)


class VectorizationAgent(BaseAgent):
    """Agente responsável por gerar embeddings."""
    
    def __init__(self, embedding_client=None, model: str = "gemini-embedding-001", dimension: int = 768):
        super().__init__(
            name="VectorizationAgent",
            description="Gera embeddings para textos",
            capabilities=["embed_text", "embed_batch"]
        )
        self.client = embedding_client
        self.model = model
        self.dimension = dimension
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        embedding = await self.embed_text(request.content)
        return AgentResponse(
            content=f"Embedding gerado: dim={len(embedding) if embedding else 0}",
            agent_name=self.name,
            metadata={"dimension": len(embedding) if embedding else 0}
        )
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Gera embedding para texto."""
        if not text:
            return None
        
        if not self.client:
            # Fallback: embedding fake para testes
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            return [(hash_val >> i) % 1000 / 1000 for i in range(self.dimension)]
        
        try:
            response = await self.client.embed(text, model=self.model)
            return response
        except Exception as e:
            logger.error("embed_failed", error=str(e))
            return None
    
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Gera embeddings em lote."""
        return [await self.embed_text(text) for text in texts]
    
    def create_embedding_entity(self, document_id: str, vector: List[float]) -> Embedding:
        """Cria entidade Embedding."""
        return Embedding(document_id=document_id, vector=vector, model=self.model)
