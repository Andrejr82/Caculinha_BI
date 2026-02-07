"""
RankingAgent — Agente de Ranking

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List, Tuple
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.ports.ranking_port import IRankingPort, RankedDocument
from backend.domain.entities.document import Document

logger = structlog.get_logger(__name__)


class RankingAgent(BaseAgent):
    """Agente responsável por ranking de documentos."""
    
    def __init__(self, ranking_port: IRankingPort):
        super().__init__(
            name="RankingAgent",
            description="Ranqueia documentos por relevância",
            capabilities=["rank_bm25", "rank_neural", "rank_hybrid", "rrf"]
        )
        self.ranker = ranking_port
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            content="Ranking agent ready",
            agent_name=self.name
        )
    
    async def rank_documents(
        self, query: str, documents: List[Document], top_k: int = 10
    ) -> List[RankedDocument]:
        """Ranqueia documentos usando BM25."""
        return await self.ranker.rank_bm25(query, documents, top_k)
    
    async def rank_with_embeddings(
        self, query: str, query_embedding: List[float],
        documents: List[Tuple[Document, List[float]]], top_k: int = 10, alpha: float = 0.5
    ) -> List[RankedDocument]:
        """Ranking híbrido com embeddings."""
        return await self.ranker.rank_hybrid(query, query_embedding, documents, top_k, alpha)
    
    async def fuse_rankings(
        self, rankings: List[List[RankedDocument]], k: int = 60, top_k: int = 10
    ) -> List[RankedDocument]:
        """Combina rankings usando RRF."""
        return await self.ranker.reciprocal_rank_fusion(rankings, k, top_k)
    
    async def rerank(self, query: str, documents: List[RankedDocument], top_k: int = 5) -> List[RankedDocument]:
        """Re-ranking final."""
        return await self.ranker.rerank(query, documents, top_k)
