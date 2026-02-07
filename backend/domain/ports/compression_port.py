"""
ICompressionPort — Interface de Compressão de Contexto

Define contrato para compressão e sumarização de contexto.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from backend.domain.entities.message import Message


@dataclass
class CompressedContext:
    """Resultado de compressão de contexto."""
    summary: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    preserved_messages: List[Message]


class ICompressionPort(ABC):
    """
    Interface para compressão de contexto.
    
    Responsabilidades:
    - Sumarização de mensagens
    - Compressão de contexto longo
    - Preservação de informações críticas
    """
    
    @abstractmethod
    async def compress_messages(
        self,
        messages: List[Message],
        max_tokens: int = 2000,
        preserve_recent: int = 3,
    ) -> CompressedContext:
        """
        Comprime lista de mensagens.
        
        Args:
            messages: Mensagens a comprimir
            max_tokens: Máximo de tokens no resultado
            preserve_recent: Número de mensagens recentes a preservar intactas
        
        Returns:
            CompressedContext com sumário e mensagens preservadas
        """
        pass
    
    @abstractmethod
    async def summarize_conversation(
        self,
        messages: List[Message],
        focus: Optional[str] = None,
    ) -> str:
        """
        Gera sumário de uma conversa.
        
        Args:
            messages: Mensagens da conversa
            focus: Foco opcional para o sumário
        
        Returns:
            Sumário textual
        """
        pass
    
    @abstractmethod
    async def extract_key_points(
        self,
        messages: List[Message],
        max_points: int = 5,
    ) -> List[str]:
        """
        Extrai pontos-chave de uma conversa.
        
        Args:
            messages: Mensagens da conversa
            max_points: Máximo de pontos a extrair
        
        Returns:
            Lista de pontos-chave
        """
        pass
    
    @abstractmethod
    async def should_compress(
        self,
        messages: List[Message],
        threshold_tokens: int = 4000,
    ) -> bool:
        """
        Verifica se compressão é necessária.
        
        Args:
            messages: Mensagens a verificar
            threshold_tokens: Limite de tokens
        
        Returns:
            True se deve comprimir
        """
        pass
    
    @abstractmethod
    async def incremental_compress(
        self,
        existing_summary: str,
        new_messages: List[Message],
    ) -> str:
        """
        Atualiza sumário existente com novas mensagens.
        
        Args:
            existing_summary: Sumário atual
            new_messages: Novas mensagens a incorporar
        
        Returns:
            Sumário atualizado
        """
        pass
