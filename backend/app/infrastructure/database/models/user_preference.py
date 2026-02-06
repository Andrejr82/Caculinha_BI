"""
User Preference Model
SQLAlchemy model for user preferences and memory
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.config.database import Base


class UserPreference(Base):
    """User preference model for storing user-specific preferences and memory"""

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)  # Additional context
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, key={self.key})>"

    # Common preference keys
    class Keys:
        """Common preference key constants"""
        PREFERRED_CHART_TYPE = "preferred_chart_type"  # bar, line, pie, scatter
        PREFERRED_DATA_FORMAT = "preferred_data_format"  # table, chart, both
        LANGUAGE = "language"  # pt-BR, en-US
        THEME = "theme"  # light, dark
        COMPANY_NAME = "company_name"
        BUSINESS_SEGMENT = "business_segment"
        ANALYSIS_FOCUS = "analysis_focus"  # sales, inventory, finance
        NOTIFICATION_ENABLED = "notification_enabled"  # true, false
