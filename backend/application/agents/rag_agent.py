"""
RAGAgent — Agente de Retrieval-Augmented Generation

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List, Optional, Dict, Any
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.ports.vector_repository_port import IVectorRepository
from backend.domain.entities.memory_entry import MemoryEntry

logger = structlog.get_logger(__name__)


class RAGAgent(BaseAgent):
    """Agente responsável por busca e recuperação de contexto."""
    
    def __init__(self, vector_repository: IVectorRepository, vectorization_agent=None):
        super().__init__(
            name="RAGAgent",
            description="Busca e recupera contexto relevante",
            capabilities=["search", "retrieve", "augment"]
        )
        self.vector_repo = vector_repository
        self.vectorization = vectorization_agent
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        results = await self.search(request.content, tenant_id=request.tenant_id, limit=5)
        context = self._format_context(results)
        return AgentResponse(
            content=context,
            agent_name=self.name,
            metadata={"results_count": len(results)}
        )
    
    async def search(
        self, query: str, tenant_id: Optional[str] = None, 
        conversation_id: Optional[str] = None, limit: int = 5
    ) -> List[MemoryEntry]:
        """Busca semântica por contexto relevante."""
        if self.vectorization:
            embedding = await self.vectorization.embed_text(query)
            if embedding:
                return await self.vector_repo.search_similar(
                    embedding, limit=limit, tenant_id=tenant_id, conversation_id=conversation_id
                )
        # Fallback: busca textual
        return await self.vector_repo.search_by_content(query, limit=limit, tenant_id=tenant_id)
    
    async def hybrid_search(
        self, query: str, tenant_id: Optional[str] = None, limit: int = 5, alpha: float = 0.5
    ) -> List[MemoryEntry]:
        """Busca híbrida (vetorial + BM25)."""
        if not self.vectorization:
            return await self.vector_repo.search_by_content(query, limit=limit)
        
        embedding = await self.vectorization.embed_text(query)
        if not embedding:
            return await self.vector_repo.search_by_content(query, limit=limit)
        
        results = await self.vector_repo.hybrid_search(query, embedding, limit=limit, tenant_id=tenant_id, alpha=alpha)
        return [entry for entry, _ in results]
    
    def _format_context(self, entries: List[MemoryEntry]) -> str:
        """Formata entradas como contexto para LLM."""
        if not entries:
            return ""
        parts = ["### Contexto Relevante:\n"]
        for i, entry in enumerate(entries, 1):
            parts.append(f"{i}. {entry.content[:500]}...")
        return "\n".join(parts)
    
    def augment_prompt(self, prompt: str, context: str) -> str:
        """Aumenta prompt com contexto recuperado."""
        if not context:
            return prompt
        return f"{context}\n\n### Pergunta:\n{prompt}"
