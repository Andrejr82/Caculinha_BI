"""
SQLServerPyTDSMemoryAdapter — Adapter de Memória usando SQLAlchemy + pytds.

Usado como fallback local quando o stack ODBC/OLE DB do Windows não consegue
estabelecer conexão, mas o SQL Server está acessível por TDS puro.
"""

import json
from typing import List, Optional

import structlog
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.config.database import Base
from backend.app.infrastructure.database.models.chat_conversation import ChatConversation
from backend.app.infrastructure.database.models.chat_feedback import ChatFeedback
from backend.app.infrastructure.database.models.chat_message import ChatMessage
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message
from backend.domain.ports.memory_repository_port import IMemoryRepository

logger = structlog.get_logger(__name__)


class SQLServerPyTDSMemoryAdapter(IMemoryRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self._initialized = False

    async def _ensure_initialized(self):
        if self._initialized:
            return
        chat_tables = [
            ChatConversation.__table__,
            ChatMessage.__table__,
            ChatFeedback.__table__,
        ]
        Base.metadata.create_all(self.engine, tables=chat_tables)
        self._initialized = True
        logger.info("sqlserver_pytds_memory_initialized")

    @staticmethod
    def _serialize_metadata(payload):
        return json.dumps(payload, ensure_ascii=False, default=str) if payload else None

    @staticmethod
    def _deserialize_metadata(payload):
        if not payload:
            return None
        try:
            return json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _to_conversation_entity(row: ChatConversation) -> Conversation:
        return Conversation(
            id=row.id,
            tenant_id=row.tenant_id,
            user_id=row.user_id,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            metadata=SQLServerPyTDSMemoryAdapter._deserialize_metadata(row.metadata_json),
        )

    @staticmethod
    def _to_message_entity(row: ChatMessage) -> Message:
        return Message(
            id=row.id,
            conversation_id=row.conversation_id,
            role=row.role,
            content=row.content,
            timestamp=row.timestamp,
            metadata=SQLServerPyTDSMemoryAdapter._deserialize_metadata(row.metadata_json),
        )

    async def save_feedback(self, request_id: str, rating: int, comment: Optional[str] = None) -> bool:
        await self._ensure_initialized()
        with self.session_factory() as session:
            existing = session.get(ChatFeedback, request_id)
            if existing is None:
                existing = ChatFeedback(request_id=request_id, rating=rating, comment=comment)
                session.add(existing)
            else:
                existing.rating = rating
                existing.comment = comment
            session.commit()
        return True

    async def save_conversation(self, conversation: Conversation) -> str:
        await self._ensure_initialized()
        with self.session_factory() as session:
            existing = session.get(ChatConversation, conversation.id)
            if existing is None:
                existing = ChatConversation(
                    id=conversation.id,
                    tenant_id=conversation.tenant_id,
                    user_id=conversation.user_id,
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    metadata_json=self._serialize_metadata(conversation.metadata),
                )
                session.add(existing)
            else:
                existing.tenant_id = conversation.tenant_id
                existing.user_id = conversation.user_id
                existing.title = conversation.title
                existing.updated_at = conversation.updated_at
                existing.metadata_json = self._serialize_metadata(conversation.metadata)
            session.commit()
        return conversation.id

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        await self._ensure_initialized()
        with self.session_factory() as session:
            row = session.get(ChatConversation, conversation_id)
            if row is None:
                return None
            return self._to_conversation_entity(row)

    async def update_conversation(self, conversation: Conversation) -> bool:
        conversation.update_timestamp()
        await self.save_conversation(conversation)
        return True

    async def delete_conversation(self, conversation_id: str) -> bool:
        await self._ensure_initialized()
        with self.session_factory() as session:
            session.execute(delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id))
            result = session.execute(delete(ChatConversation).where(ChatConversation.id == conversation_id))
            session.commit()
            return (result.rowcount or 0) > 0

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        await self._ensure_initialized()
        stmt = (
            select(ChatConversation)
            .where(ChatConversation.tenant_id == tenant_id)
            .order_by(ChatConversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(ChatConversation.user_id == user_id)

        with self.session_factory() as session:
            rows = session.execute(stmt).scalars().all()
            return [self._to_conversation_entity(row) for row in rows]

    async def add_message(self, message: Message) -> str:
        await self._ensure_initialized()
        with self.session_factory() as session:
            session.add(
                ChatMessage(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content,
                    timestamp=message.timestamp,
                    metadata_json=self._serialize_metadata(message.metadata),
                )
            )
            session.commit()
        return message.id

    async def get_message(self, message_id: str) -> Optional[Message]:
        await self._ensure_initialized()
        with self.session_factory() as session:
            row = session.get(ChatMessage, message_id)
            if row is None:
                return None
            return self._to_message_entity(row)

    async def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Message]:
        await self._ensure_initialized()
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
        )
        with self.session_factory() as session:
            rows = list(reversed(session.execute(stmt).scalars().all()))
            return [self._to_message_entity(row) for row in rows]

    async def get_all_messages(self, conversation_id: str) -> List[Message]:
        await self._ensure_initialized()
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.timestamp.asc())
        )
        with self.session_factory() as session:
            rows = session.execute(stmt).scalars().all()
            return [self._to_message_entity(row) for row in rows]

    async def delete_message(self, message_id: str) -> bool:
        await self._ensure_initialized()
        with self.session_factory() as session:
            result = session.execute(delete(ChatMessage).where(ChatMessage.id == message_id))
            session.commit()
            return (result.rowcount or 0) > 0

    async def count_messages(self, conversation_id: str) -> int:
        await self._ensure_initialized()
        stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        with self.session_factory() as session:
            return int(session.execute(stmt).scalar_one() or 0)
