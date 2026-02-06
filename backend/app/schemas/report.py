"""
Report Schemas
Pydantic schemas for Report API
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    """Base report schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ReportCreate(ReportBase):
    """Schema for creating a report"""

    content: dict = Field(default_factory=dict)  # TipTap JSON
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")


class ReportUpdate(BaseModel):
    """Schema for updating a report"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    content: dict | None = None
    status: str | None = Field(None, pattern="^(draft|published|archived)$")


class ReportResponse(ReportBase):
    """Schema for report response"""

    id: uuid.UUID
    content: dict
    status: str
    author_id: uuid.UUID
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Schema for report list response"""

    id: uuid.UUID
    title: str
    description: str | None
    status: str
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
