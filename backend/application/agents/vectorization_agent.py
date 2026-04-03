"""
VectorizationAgent — Agente de Vetorização

Autor: Orchestrator Agent
Data: 2026-02-07
"""

import inspect
from typing import List, Optional
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.app.config.settings import settings
from backend.app.core.retrieval.embedding_backend import get_embedding_backend
from backend.domain.entities.embedding import Embedding

logger = structlog.get_logger(__name__)


class VectorizationAgent(BaseAgent):
    """Agente responsável por gerar embeddings."""
    
    def __init__(self, embedding_client=None, model: Optional[str] = None, dimension: Optional[int] = None):
        super().__init__(
            name="VectorizationAgent",
            description="Gera embeddings para textos",
            capabilities=["embed_text", "embed_batch"]
        )
        self.client = embedding_client
        self.model = model or settings.RAG_EMBEDDING_MODEL
        self.embedding_backend = get_embedding_backend(model_name=self.model)
        self.dimension = dimension or self.embedding_backend.dimension
    
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
        
        try:
            if self.client and hasattr(self.client, "embed"):
                response = self.client.embed(text, model=self.model)
                if inspect.isawaitable(response):
                    response = await response
                if response:
                    return response

            vector = self.embedding_backend.embed_text(text)
            if vector:
                self.dimension = len(vector)
            return vector or None
        except Exception as e:
            logger.error("embed_failed", error=str(e))
            return None
    
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Gera embeddings em lote."""
        return [await self.embed_text(text) for text in texts]
    
    def create_embedding_entity(self, document_id: str, vector: List[float]) -> Embedding:
        """Cria entidade Embedding."""
        return Embedding(document_id=document_id, vector=vector, model=self.model)
