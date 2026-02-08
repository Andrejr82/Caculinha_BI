"""
SQLiteMemoryAdapter — Adapter de Memória SQLite

Implementação de persistência de longo prazo usando SQLite.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import json
import sqlite3
import aiosqlite
from typing import List, Optional
from datetime import datetime
from pathlib import Path

import structlog

from backend.domain.ports.memory_repository_port import IMemoryRepository
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message


logger = structlog.get_logger(__name__)


class SQLiteMemoryAdapter(IMemoryRepository):
    """
    Adapter SQLite para persistência de memória de longo prazo.
    
    Usa SQLite para armazenamento permanente de conversas e mensagens.
    Ideal para: histórico completo, auditoria, persistência.
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        """
        Inicializa o adapter SQLite.
        
        Args:
            db_path: Caminho para o arquivo do banco
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Garante que as tabelas existem."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_conv_tenant 
                    ON conversations(tenant_id, updated_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_conv_user 
                    ON conversations(tenant_id, user_id, updated_at DESC);
                
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_msg_conv 
                    ON messages(conversation_id, timestamp ASC);
                
                CREATE TABLE IF NOT EXISTS feedbacks (
                    request_id TEXT PRIMARY KEY,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL
                );
            """)
            await db.commit()
        
        self._initialized = True
        logger.info("sqlite_memory_initialized", db_path=str(self.db_path))
    
    # ... existing code ...

    async def save_feedback(self, request_id: str, rating: int, comment: Optional[str] = None) -> bool:
        """Salva feedback do usuário no SQLite."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO feedbacks (request_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                request_id,
                rating,
                comment,
                datetime.utcnow().isoformat()
            ))
            await db.commit()
            return True
    
    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================
    
    async def save_conversation(self, conversation: Conversation) -> str:
        """Salva conversa no SQLite."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, tenant_id, user_id, title, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation.id,
                conversation.tenant_id,
                conversation.user_id,
                conversation.title,
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat(),
                json.dumps(conversation.metadata) if conversation.metadata else None,
            ))
            await db.commit()
        
        logger.debug("conversation_saved_sqlite", conversation_id=conversation.id)
        return conversation.id
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Recupera conversa do SQLite."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
        
        if not row:
            return None
        
        return Conversation(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        )
    
    async def update_conversation(self, conversation: Conversation) -> bool:
        """Atualiza conversa no SQLite."""
        conversation.update_timestamp()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE conversations 
                SET title = ?, updated_at = ?, metadata = ?
                WHERE id = ?
            """, (
                conversation.title,
                conversation.updated_at.isoformat(),
                json.dumps(conversation.metadata) if conversation.metadata else None,
                conversation.id,
            ))
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta conversa e suas mensagens."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Deleta mensagens primeiro
            await db.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            # Deleta conversa
            cursor = await db.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """Lista conversas de um tenant."""
        await self._ensure_initialized()
        
        if user_id:
            query = """
                SELECT * FROM conversations 
                WHERE tenant_id = ? AND user_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = (tenant_id, user_id, limit, offset)
        else:
            query = """
                SELECT * FROM conversations 
                WHERE tenant_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = (tenant_id, limit, offset)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
        
        return [
            Conversation(
                id=row["id"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
            for row in rows
        ]
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    async def add_message(self, message: Message) -> str:
        """Adiciona mensagem ao SQLite."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages 
                (id, conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.conversation_id,
                message.role,
                message.content,
                message.timestamp.isoformat(),
                json.dumps(message.metadata) if message.metadata else None,
            ))
            await db.commit()
        
        return message.id
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Recupera mensagem do SQLite."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM messages WHERE id = ?",
                (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
        
        if not row:
            return None
        
        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        )
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """Recupera mensagens recentes."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, limit)) as cursor:
                rows = await cursor.fetchall()
        
        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
            for row in rows
        ]
    
    async def get_all_messages(self, conversation_id: str) -> List[Message]:
        """Recupera todas as mensagens."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """, (conversation_id,)) as cursor:
                rows = await cursor.fetchall()
        
        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
            for row in rows
        ]
    
    async def delete_message(self, message_id: str) -> bool:
        """Deleta uma mensagem."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM messages WHERE id = ?",
                (message_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def count_messages(self, conversation_id: str) -> int:
        """Conta mensagens de uma conversa."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
