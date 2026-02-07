"""
IVectorRepository Port — Interface de Repositório Vetorial

Define contrato para busca semântica e indexação de embeddings.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from backend.domain.entities.memory_entry import MemoryEntry
from backend.domain.entities.document import Document
from backend.domain.entities.embedding import Embedding


class IVectorRepository(ABC):
    """
    Interface para repositório de busca vetorial.
    
    Responsabilidades:
    - Indexação de embeddings
    - Busca por similaridade
    - Gerenciamento de índices
    """
    
    # =========================================================================
    # INDEXING OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def index_entry(self, entry: MemoryEntry) -> str:
        """
        Indexa uma entrada de memória.
        
        Args:
            entry: Entrada com embedding
        
        Returns:
            ID da entrada indexada
        """
        pass
    
    @abstractmethod
    async def index_document(self, document: Document, embedding: Embedding) -> str:
        """
        Indexa um documento com seu embedding.
        
        Args:
            document: Documento a indexar
            embedding: Embedding do documento
        
        Returns:
            ID do documento indexado
        """
        pass
    
    @abstractmethod
    async def batch_index(self, entries: List[MemoryEntry]) -> List[str]:
        """
        Indexa múltiplas entradas em lote.
        
        Args:
            entries: Lista de entradas
        
        Returns:
            Lista de IDs indexados
        """
        pass
    
    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        tenant_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[MemoryEntry]:
        """
        Busca entradas similares por embedding.
        
        Args:
            query_embedding: Vetor de query
            limit: Máximo de resultados
            tenant_id: Filtrar por tenant
            conversation_id: Filtrar por conversa
            min_score: Score mínimo (0-1)
        
        Returns:
            Lista de MemoryEntry ordenada por score DESC
        """
        pass
    
    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """
        Busca por conteúdo textual (fallback sem embedding).
        
        Args:
            query: Texto de busca
            limit: Máximo de resultados
            tenant_id: Filtrar por tenant
        
        Returns:
            Lista de MemoryEntry
        """
        pass
    
    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        limit: int = 5,
        tenant_id: Optional[str] = None,
        alpha: float = 0.5,
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Busca híbrida (BM25 + vetorial).
        
        Args:
            query: Texto de busca
            query_embedding: Vetor de query
            limit: Máximo de resultados
            tenant_id: Filtrar por tenant
            alpha: Peso do vetorial (0=BM25, 1=vetorial)
        
        Returns:
            Lista de (MemoryEntry, score) combinado
        """
        pass
    
    # =========================================================================
    # MANAGEMENT OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def delete_by_conversation(self, conversation_id: str) -> int:
        """
        Deleta todas as entradas de uma conversa.
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            Número de entradas deletadas
        """
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """
        Deleta embedding de um documento.
        
        Args:
            document_id: ID do documento
        
        Returns:
            Número de entradas deletadas
        """
        pass
    
    @abstractmethod
    async def count_entries(self, tenant_id: Optional[str] = None) -> int:
        """
        Conta entradas indexadas.
        
        Args:
            tenant_id: Filtrar por tenant
        
        Returns:
            Número de entradas
        """
        pass
    
    @abstractmethod
    async def get_index_stats(self) -> dict:
        """
        Retorna estatísticas do índice.
        
        Returns:
            Dict com total_entries, dimension, index_size, etc.
        """
        pass
