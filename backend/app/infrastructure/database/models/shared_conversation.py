"""
Shared Conversation Model
SQLAlchemy model for shared conversations
"""

import uuid
from datetime import datetime, timedelta
import json

from sqlalchemy import Boolean, DateTime, String, Uuid, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.config.database import Base


class SharedConversation(Base):
    """Shared conversation database model for public conversation links"""

    __tablename__ = "shared_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    share_id: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    messages: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    view_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SharedConversation(share_id={self.share_id}, session_id={self.session_id})>"

    @property
    def messages_list(self) -> list[dict]:
        """Converte a string JSON de messages para uma lista Python."""
        try:
            return json.loads(self.messages) if self.messages else []
        except (json.JSONDecodeError, TypeError):
            return []

    @messages_list.setter
    def messages_list(self, messages: list[dict]):
        """Define messages a partir de uma lista Python, convertendo para string JSON."""
        self.messages = json.dumps(messages) if messages is not None else "[]"

    @property
    def is_expired(self) -> bool:
        """Check if the shared conversation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def increment_view_count(self):
        """Increment the view counter."""
        self.view_count += 1
