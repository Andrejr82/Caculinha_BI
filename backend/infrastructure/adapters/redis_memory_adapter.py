"""
RedisMemoryAdapter — Adapter de Memória Redis

Implementação de cache de curto prazo usando Redis.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import json
from typing import List, Optional
from datetime import datetime

import structlog

from backend.domain.ports.memory_repository_port import IMemoryRepository
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message


logger = structlog.get_logger(__name__)


class RedisMemoryAdapter(IMemoryRepository):
    """
    Adapter Redis para cache de memória de curto prazo.
    
    Usa Redis como cache com TTL para acesso rápido a conversas ativas.
    Ideal para: sessões ativas, contexto imediato, warm cache.
    """
    
    def __init__(
        self,
        redis_client=None,
        prefix: str = "memory:",
        conversation_ttl: int = 3600,  # 1 hora
        message_ttl: int = 3600,
    ):
        """
        Inicializa o adapter Redis.
        
        Args:
            redis_client: Cliente Redis (aioredis)
            prefix: Prefixo para chaves
            conversation_ttl: TTL de conversas em segundos
            message_ttl: TTL de mensagens em segundos
        """
        self.redis = redis_client
        self.prefix = prefix
        self.conversation_ttl = conversation_ttl
        self.message_ttl = message_ttl
    
    def _key(self, *parts: str) -> str:
        """Gera chave Redis."""
        return self.prefix + ":".join(parts)
    
    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================
    
    async def save_conversation(self, conversation: Conversation) -> str:
        """Salva conversa no Redis."""
        key = self._key("conv", conversation.id)
        data = json.dumps(conversation.to_dict())
        
        if self.redis:
            await self.redis.setex(key, self.conversation_ttl, data)
            
            # Adiciona ao índice do tenant
            index_key = self._key("tenant", conversation.tenant_id, "convs")
            await self.redis.zadd(
                index_key, 
                {conversation.id: conversation.updated_at.timestamp()}
            )
        
        logger.debug("conversation_saved_redis", conversation_id=conversation.id)
        return conversation.id
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Recupera conversa do Redis."""
        if not self.redis:
            return None
        
        key = self._key("conv", conversation_id)
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        return Conversation.from_dict(json.loads(data))
    
    async def update_conversation(self, conversation: Conversation) -> bool:
        """Atualiza conversa no Redis."""
        conversation.update_timestamp()
        await self.save_conversation(conversation)
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta conversa do Redis."""
        if not self.redis:
            return False
        
        key = self._key("conv", conversation_id)
        result = await self.redis.delete(key)
        
        # Deleta mensagens da conversa
        msg_pattern = self._key("msgs", conversation_id, "*")
        async for msg_key in self.redis.scan_iter(msg_pattern):
            await self.redis.delete(msg_key)
        
        return result > 0
    
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """Lista conversas de um tenant."""
        if not self.redis:
            return []
        
        index_key = self._key("tenant", tenant_id, "convs")
        conv_ids = await self.redis.zrevrange(
            index_key, offset, offset + limit - 1
        )
        
        conversations = []
        for conv_id in conv_ids:
            conv = await self.get_conversation(conv_id)
            if conv and (not user_id or conv.user_id == user_id):
                conversations.append(conv)
        
        return conversations
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    async def add_message(self, message: Message) -> str:
        """Adiciona mensagem ao Redis."""
        if not self.redis:
            return message.id
        
        # Salva mensagem
        key = self._key("msg", message.id)
        data = json.dumps(message.to_dict())
        await self.redis.setex(key, self.message_ttl, data)
        
        # Adiciona ao índice da conversa
        index_key = self._key("msgs", message.conversation_id)
        await self.redis.zadd(
            index_key,
            {message.id: message.timestamp.timestamp()}
        )
        
        return message.id
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Recupera mensagem do Redis."""
        if not self.redis:
            return None
        
        key = self._key("msg", message_id)
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        return Message.from_dict(json.loads(data))
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """Recupera mensagens recentes."""
        if not self.redis:
            return []
        
        index_key = self._key("msgs", conversation_id)
        msg_ids = await self.redis.zrange(index_key, -limit, -1)
        
        messages = []
        for msg_id in msg_ids:
            msg = await self.get_message(msg_id)
            if msg:
                messages.append(msg)
        
        return messages
    
    async def get_all_messages(self, conversation_id: str) -> List[Message]:
        """Recupera todas as mensagens."""
        if not self.redis:
            return []
        
        index_key = self._key("msgs", conversation_id)
        msg_ids = await self.redis.zrange(index_key, 0, -1)
        
        messages = []
        for msg_id in msg_ids:
            msg = await self.get_message(msg_id)
            if msg:
                messages.append(msg)
        
        return messages
    
    async def delete_message(self, message_id: str) -> bool:
        """Deleta uma mensagem."""
        if not self.redis:
            return False
        
        key = self._key("msg", message_id)
        result = await self.redis.delete(key)
        return result > 0
    
    async def count_messages(self, conversation_id: str) -> int:
        """Conta mensagens de uma conversa."""
        if not self.redis:
            return 0
        
        index_key = self._key("msgs", conversation_id)
        return await self.redis.zcard(index_key)
