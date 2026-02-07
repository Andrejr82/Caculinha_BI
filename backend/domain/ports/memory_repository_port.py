"""
IMemoryRepository Port — Interface de Repositório de Memória

Define contrato para persistência de conversas e mensagens.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message


class IMemoryRepository(ABC):
    """
    Interface para repositório de memória conversacional.
    
    Responsabilidades:
    - CRUD de conversas
    - Gerenciamento de mensagens
    - Listagem e busca
    """
    
    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> str:
        """
        Salva uma conversa.
        
        Args:
            conversation: Entidade de conversa
        
        Returns:
            ID da conversa salva
        """
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Recupera uma conversa por ID.
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            Conversation ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> bool:
        """
        Atualiza uma conversa existente.
        
        Args:
            conversation: Conversa com dados atualizados
        
        Returns:
            True se atualizada, False se não encontrada
        """
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deleta uma conversa e todas suas mensagens.
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            True se deletada, False se não encontrada
        """
        pass
    
    @abstractmethod
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        Lista conversas de um tenant/usuário.
        
        Args:
            tenant_id: ID do tenant
            user_id: Filtrar por usuário (opcional)
            limit: Máximo de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de conversas ordenadas por updated_at DESC
        """
        pass
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def add_message(self, message: Message) -> str:
        """
        Adiciona uma mensagem a uma conversa.
        
        Args:
            message: Entidade de mensagem
        
        Returns:
            ID da mensagem salva
        """
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[Message]:
        """
        Recupera uma mensagem por ID.
        
        Args:
            message_id: ID da mensagem
        
        Returns:
            Message ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """
        Recupera mensagens recentes de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            limit: Máximo de mensagens
        
        Returns:
            Lista de mensagens ordenadas por timestamp ASC
        """
        pass
    
    @abstractmethod
    async def get_all_messages(
        self,
        conversation_id: str,
    ) -> List[Message]:
        """
        Recupera todas as mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            Lista completa de mensagens
        """
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """
        Deleta uma mensagem.
        
        Args:
            message_id: ID da mensagem
        
        Returns:
            True se deletada, False se não encontrada
        """
        pass
    
    @abstractmethod
    async def count_messages(self, conversation_id: str) -> int:
        """
        Conta mensagens em uma conversa.
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            Número de mensagens
        """
        pass
