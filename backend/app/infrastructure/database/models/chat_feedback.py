"""
Chat Feedback Model
SQLAlchemy model for persisted chat feedback events.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.config.database import Base


class ChatFeedback(Base):
    __tablename__ = "chat_feedbacks"

    request_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
