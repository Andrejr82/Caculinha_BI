"""
IRankingPort — Interface de Ranking

Define contrato para ranking de documentos (BM25, Neural, RRF).

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass

from backend.domain.entities.document import Document


@dataclass
class RankedDocument:
    """Documento com score de ranking."""
    document: Document
    score: float
    rank: int
    method: str  # "bm25", "neural", "rrf"


class IRankingPort(ABC):
    """
    Interface para ranking de documentos.
    
    Responsabilidades:
    - BM25 ranking (sparse)
    - Neural ranking (dense)
    - Reciprocal Rank Fusion (RRF)
    """
    
    @abstractmethod
    async def rank_bm25(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """
        Ranking usando BM25 (sparse retrieval).
        
        Args:
            query: Query de busca
            documents: Documentos candidatos
            top_k: Top K resultados
        
        Returns:
            Lista ordenada por score BM25 DESC
        """
        pass
    
    @abstractmethod
    async def rank_neural(
        self,
        query_embedding: List[float],
        documents: List[Tuple[Document, List[float]]],
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """
        Ranking usando similaridade neural (dense retrieval).
        
        Args:
            query_embedding: Embedding da query
            documents: Lista de (Document, embedding)
            top_k: Top K resultados
        
        Returns:
            Lista ordenada por similaridade DESC
        """
        pass
    
    @abstractmethod
    async def rank_hybrid(
        self,
        query: str,
        query_embedding: List[float],
        documents: List[Tuple[Document, List[float]]],
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> List[RankedDocument]:
        """
        Ranking híbrido combinando BM25 e neural.
        
        Args:
            query: Query de busca
            query_embedding: Embedding da query
            documents: Lista de (Document, embedding)
            top_k: Top K resultados
            alpha: Peso do neural (0=BM25, 1=neural)
        
        Returns:
            Lista ordenada por score combinado DESC
        """
        pass
    
    @abstractmethod
    async def reciprocal_rank_fusion(
        self,
        rankings: List[List[RankedDocument]],
        k: int = 60,
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """
        Combina múltiplos rankings usando RRF.
        
        RRF(d) = Σ 1 / (k + rank_i(d))
        
        Args:
            rankings: Lista de rankings a combinar
            k: Constante RRF (default 60)
            top_k: Top K resultados finais
        
        Returns:
            Lista ordenada por score RRF DESC
        """
        pass
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[RankedDocument],
        top_k: int = 5,
    ) -> List[RankedDocument]:
        """
        Re-ranking usando cross-encoder (mais preciso, mais lento).
        
        Args:
            query: Query original
            documents: Documentos pré-rankeados
            top_k: Top K resultados finais
        
        Returns:
            Lista re-ordenada por relevância
        """
        pass
