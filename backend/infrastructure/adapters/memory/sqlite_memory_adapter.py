"""
SQLiteMemoryAdapter — Adapter de Memória com SQLite

Implementa MemoryRepositoryPort usando SQLite para persistência.

Uso:
    from backend.infrastructure.adapters.memory import SQLiteMemoryAdapter
    
    adapter = SQLiteMemoryAdapter(db_path="memory.db")
    await adapter.save_conversation(conversation)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import asyncio

import structlog

from backend.domain.ports.memory_repository_port import MemoryRepositoryPort
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message


logger = structlog.get_logger(__name__)


class SQLiteMemoryAdapter(MemoryRepositoryPort):
    """
    Adapter de memória usando SQLite.
    
    Implementação de MemoryRepositoryPort para persistência local.
    Ideal para desenvolvimento e deploys simples.
    """
    
    def __init__(self, db_path: str = "memory.db"):
        """
        Inicializa o adapter SQLite.
        
        Args:
            db_path: Caminho para o arquivo de banco de dados
        """
        self.db_path = Path(db_path)
        self._initialized = False
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão SQLite."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def _ensure_tables(self):
        """Garante que as tabelas existem."""
        if self._initialized:
            return
        
        conn = self._get_connection()
        try:
            conn.executescript("""
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
                    ON conversations(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_conv_user 
                    ON conversations(tenant_id, user_id);
                
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
                    ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_msg_timestamp 
                    ON messages(conversation_id, timestamp);
            """)
            conn.commit()
            self._initialized = True
            logger.info("sqlite_tables_created", db_path=str(self.db_path))
        finally:
            conn.close()
    
    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================
    
    async def save_conversation(self, conversation: Conversation) -> str:
        """Salva conversa no SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            conn.execute("""
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
            conn.commit()
            logger.debug("conversation_saved", conversation_id=conversation.id)
            return conversation.id
        finally:
            conn.close()
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Busca conversa do SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
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
        finally:
            conn.close()
    
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """Lista conversas do SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            if user_id:
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    WHERE tenant_id = ? AND user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (tenant_id, user_id, limit, offset))
            else:
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    WHERE tenant_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (tenant_id, limit, offset))
            
            rows = cursor.fetchall()
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
        finally:
            conn.close()
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta conversa e mensagens do SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            # Deleta mensagens primeiro
            conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            # Deleta conversa
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("conversation_deleted", conversation_id=conversation_id)
            return deleted
        finally:
            conn.close()
    
    async def update_conversation(self, conversation: Conversation) -> bool:
        """Atualiza conversa no SQLite."""
        conversation.update_timestamp()
        await self.save_conversation(conversation)
        return True
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    async def add_message(self, message: Message) -> str:
        """Adiciona mensagem ao SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            conn.execute("""
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
            conn.commit()
            logger.debug("message_added", message_id=message.id)
            return message.id
        finally:
            conn.close()
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 10,
        before_id: Optional[str] = None,
    ) -> List[Message]:
        """Busca mensagens do SQLite."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            if before_id:
                cursor = conn.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = ? 
                    AND timestamp < (SELECT timestamp FROM messages WHERE id = ?)
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (conversation_id, before_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (conversation_id, limit))
            
            rows = cursor.fetchall()
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
        finally:
            conn.close()
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[Message]:
        """Busca mensagens mais recentes."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))
            
            rows = cursor.fetchall()
            messages = [
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
            # Retorna em ordem cronológica
            return list(reversed(messages))
        finally:
            conn.close()
    
    async def count_messages(self, conversation_id: str) -> int:
        """Conta mensagens de uma conversa."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    async def delete_messages(self, conversation_id: str) -> int:
        """Deleta todas as mensagens de uma conversa."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
