"""
User Model
SQLAlchemy model for users table
"""

import uuid
from datetime import datetime
import json # Adicionado para manipulação de JSON string

from sqlalchemy import Boolean, DateTime, String, Uuid, Text # Adicionado Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.config.database import Base


class User(Base):
    """User database model"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_segments: Mapped[str] = mapped_column(Text, nullable=False, default="[]") # Armazenar como JSON string
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def segments_list(self) -> list[str]:
        """Converte a string JSON de allowed_segments para uma lista Python."""
        try:
            return json.loads(self.allowed_segments) if self.allowed_segments else []
        except (json.JSONDecodeError, TypeError):
            return []

    @segments_list.setter
    def segments_list(self, segments: list[str]):
        """Define allowed_segments a partir de uma lista Python, convertendo para string JSON."""
        self.allowed_segments = json.dumps(segments) if segments is not None else "[]"
