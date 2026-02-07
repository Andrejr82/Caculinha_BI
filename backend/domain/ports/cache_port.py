"""
Port: CachePort

Interface abstrata para caching.
Implementada por: RedisAdapter, InMemoryCache

Uso:
    from backend.domain.ports import CachePort
    
    class RedisAdapter(CachePort):
        async def get(self, key):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CachePort(ABC):
    """
    Interface abstrata para operações de cache.
    
    Esta é a porta para caching de dados.
    Implementações concretas em infrastructure/adapters/cache/
    
    Example:
        >>> class RedisAdapter(CachePort):
        ...     async def get(self, key):
        ...         return await self.client.get(key)
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave do item
        
        Returns:
            Valor ou None se não existir
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave do item
            value: Valor a armazenar
            ttl_seconds: Tempo de vida em segundos
        
        Returns:
            True se sucesso
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Remove um item do cache.
        
        Args:
            key: Chave do item
        
        Returns:
            True se removido
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe.
        
        Args:
            key: Chave a verificar
        
        Returns:
            True se existir
        """
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Limpa itens do cache.
        
        Args:
            pattern: Padrão de chaves a limpar (None = todos)
        
        Returns:
            Número de itens removidos
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica se o cache está saudável.
        
        Returns:
            True se saudável
        """
        pass
