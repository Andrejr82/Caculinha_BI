"""
RedisMemoryAdapter — Adapter de Memória com Redis

Implementa MemoryRepositoryPort usando Redis para cache de curto prazo.

Uso:
    from backend.infrastructure.adapters.memory import RedisMemoryAdapter
    
    adapter = RedisMemoryAdapter(redis_url="redis://localhost:6379")
    await adapter.save_conversation(conversation)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import json
from typing import Optional, List
from datetime import datetime

import structlog

from backend.domain.ports.memory_repository_port import MemoryRepositoryPort
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message


logger = structlog.get_logger(__name__)


class RedisMemoryAdapter(MemoryRepositoryPort):
    """
    Adapter de memória usando Redis.
    
    Implementação de MemoryRepositoryPort para cache de curto prazo.
    Usa Redis para armazenamento rápido com TTL configurável.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,  # 1 hora
        key_prefix: str = "caculinha:memory:",
    ):
        """
        Inicializa o adapter Redis.
        
        Args:
            redis_url: URL de conexão com Redis
            ttl_seconds: TTL padrão para chaves
            key_prefix: Prefixo para chaves Redis
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._client = None
    
    async def _get_client(self):
        """Obtém cliente Redis (lazy initialization)."""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.warning("redis package not installed, using mock")
                self._client = None
        return self._client
    
    def _conv_key(self, conversation_id: str) -> str:
        """Gera chave Redis para conversa."""
        return f"{self.key_prefix}conv:{conversation_id}"
    
    def _msgs_key(self, conversation_id: str) -> str:
        """Gera chave Redis para mensagens."""
        return f"{self.key_prefix}msgs:{conversation_id}"
    
    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================
    
    async def save_conversation(self, conversation: Conversation) -> str:
        """Salva conversa no Redis."""
        client = await self._get_client()
        if client is None:
            logger.warning("Redis not available, skipping save")
            return conversation.id
        
        key = self._conv_key(conversation.id)
        data = json.dumps(conversation.to_dict())
        
        await client.setex(key, self.ttl_seconds, data)
        logger.debug("conversation_saved", conversation_id=conversation.id)
        
        return conversation.id
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Busca conversa do Redis."""
        client = await self._get_client()
        if client is None:
            return None
        
        key = self._conv_key(conversation_id)
        data = await client.get(key)
        
        if data is None:
            return None
        
        return Conversation.from_dict(json.loads(data))
    
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """Lista conversas (limitado no Redis, melhor usar SQLite)."""
        client = await self._get_client()
        if client is None:
            return []
        
        # Redis não é ideal para listagens
        # Retorna lista vazia - use SQLiteMemoryAdapter para listagens
        logger.warning("list_conversations not optimized for Redis")
        return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta conversa do Redis."""
        client = await self._get_client()
        if client is None:
            return False
        
        conv_key = self._conv_key(conversation_id)
        msgs_key = self._msgs_key(conversation_id)
        
        deleted = await client.delete(conv_key, msgs_key)
        return deleted > 0
    
    async def update_conversation(self, conversation: Conversation) -> bool:
        """Atualiza conversa no Redis."""
        conversation.update_timestamp()
        await self.save_conversation(conversation)
        return True
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    async def add_message(self, message: Message) -> str:
        """Adiciona mensagem à lista Redis."""
        client = await self._get_client()
        if client is None:
            return message.id
        
        key = self._msgs_key(message.conversation_id)
        data = json.dumps(message.to_dict())
        
        # Adiciona à lista e mantém TTL
        await client.rpush(key, data)
        await client.expire(key, self.ttl_seconds)
        
        logger.debug("message_added", message_id=message.id)
        return message.id
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 10,
        before_id: Optional[str] = None,
    ) -> List[Message]:
        """Busca mensagens do Redis."""
        client = await self._get_client()
        if client is None:
            return []
        
        key = self._msgs_key(conversation_id)
        data_list = await client.lrange(key, -limit, -1)
        
        messages = [Message.from_dict(json.loads(d)) for d in data_list]
        return messages
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """Busca mensagens mais recentes."""
        return await self.get_messages(conversation_id, limit)
    
    async def count_messages(self, conversation_id: str) -> int:
        """Conta mensagens na lista Redis."""
        client = await self._get_client()
        if client is None:
            return 0
        
        key = self._msgs_key(conversation_id)
        return await client.llen(key)
    
    async def delete_messages(self, conversation_id: str) -> int:
        """Deleta mensagens do Redis."""
        client = await self._get_client()
        if client is None:
            return 0
        
        key = self._msgs_key(conversation_id)
        count = await client.llen(key)
        await client.delete(key)
        return count
