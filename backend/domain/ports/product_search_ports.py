"""
Product Search Ports — Interfaces de Recuperação e Ranqueamento

Define os contratos para indexação híbrida, fusão de scores e avaliação de qualidade de busca.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.entities.retrieval import RetrievedItem, RankingScores, RankedProduct


class IRetrievalIndexPort(ABC):
    """Porta para motores de indexação (BM25 e Vetorial)."""
    
    @abstractmethod
    async def build_index(self, products: List[ProductCanonical], version: str) -> bool:
        """Constrói o índice para uma versão específica do catálogo."""
        pass
    
    @abstractmethod
    async def search(self, query: str, version: str, top_k: int = 100) -> List[RetrievedItem]:
        """Realiza busca e retorna candidatos com scores brutos."""
        pass


class IRankingFusionPort(ABC):
    """Porta para fusão de rankings e aplicação de regras de negócio."""
    
    @abstractmethod
    async def fuse_and_rank(
        self, 
        bm25_results: List[RetrievedItem], 
        vector_results: List[RetrievedItem],
        query: str,
        weights: Optional[Dict[str, float]] = None
    ) -> List[RankedProduct]:
        """Combina múltiplos rankings e aplica boosts de regras de negócio."""
        pass


class IRerankerPort(ABC):
    """Porta para refinamento final do ranking (Reranking)."""
    
    @abstractmethod
    async def rerank(self, query: str, candidates: List[RankedProduct], top_k: int = 10) -> List[RankedProduct]:
        """Reordena o top N de candidatos para o top K final."""
        pass


class IEvaluationPort(ABC):
    """Porta para avaliação offline da qualidade do ranking."""
    
    @abstractmethod
    async def calculate_metrics(
        self, 
        queries: List[str], 
        expected_ids: List[List[int]], 
        k: int = 10
    ) -> Dict[str, float]:
        """Calcula Recall@K, MRR@K e nDCG@K."""
        pass
