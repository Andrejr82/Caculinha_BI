"""
VectorSearchPort — Interface de Busca Vetorial

Define o contrato para indexação e busca semântica de mensagens.

Uso:
    from backend.domain.ports import VectorSearchPort
    
    class DuckDBVectorAdapter(VectorSearchPort):
        async def index_message(self, message: Message, embedding: List[float]) -> str:
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from backend.domain.entities.message import Message
from backend.domain.entities.memory_entry import MemoryEntry


class VectorSearchPort(ABC):
    """
    Port de Busca Vetorial.
    
    Define o contrato para indexação e busca por similaridade semântica.
    Implementação: DuckDBVectorAdapter.
    """
    
    # =========================================================================
    # INDEXING OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def index_message(
        self,
        message: Message,
        embedding: List[float],
    ) -> str:
        """
        Indexa uma mensagem com seu embedding.
        
        Args:
            message: Mensagem a indexar
            embedding: Vetor de embedding
        
        Returns:
            ID da entrada criada
        """
        pass
    
    @abstractmethod
    async def index_entry(self, entry: MemoryEntry) -> str:
        """
        Indexa uma entrada de memória diretamente.
        
        Args:
            entry: Entrada com embedding
        
        Returns:
            ID da entrada
        """
        pass
    
    @abstractmethod
    async def update_embedding(
        self,
        entry_id: str,
        embedding: List[float],
    ) -> bool:
        """
        Atualiza o embedding de uma entrada existente.
        
        Args:
            entry_id: ID da entrada
            embedding: Novo vetor de embedding
        
        Returns:
            True se atualizada, False se não encontrada
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
        Busca mensagens similares por embedding.
        
        Args:
            query_embedding: Vetor de query
            limit: Máximo de resultados
            tenant_id: Filtrar por tenant (opcional)
            conversation_id: Filtrar por conversa (opcional)
            min_score: Score mínimo de similaridade
        
        Returns:
            Lista de MemoryEntry ordenada por score (desc)
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
        Busca por texto com full-text search.
        
        Args:
            query: Texto de busca
            limit: Máximo de resultados
            tenant_id: Filtrar por tenant (opcional)
        
        Returns:
            Lista de MemoryEntry
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
    async def delete_by_message(self, message_id: str) -> bool:
        """
        Deleta a entrada de uma mensagem específica.
        
        Args:
            message_id: ID da mensagem
        
        Returns:
            True se deletada, False se não encontrada
        """
        pass
    
    @abstractmethod
    async def count_entries(
        self,
        tenant_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """
        Conta entradas indexadas.
        
        Args:
            tenant_id: Filtrar por tenant (opcional)
            conversation_id: Filtrar por conversa (opcional)
        
        Returns:
            Número de entradas
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """
        Retorna estatísticas do índice vetorial.
        
        Returns:
            Dict com total_entries, embedding_dimension, etc.
        """
        pass
