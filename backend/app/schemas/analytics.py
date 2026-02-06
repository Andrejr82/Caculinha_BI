"""
Analytics Schemas
Pydantic schemas for Analytics API
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsFilter(BaseModel):
    """Analytics filter parameters"""

    date_start: date | None = None
    date_end: date | None = None
    category: str | None = None
    segment: str | None = None
    min_value: float | None = None
    max_value: float | None = None


class AnalyticsData(BaseModel):
    """Analytics data point"""

    id: str
    date: str
    category: str
    value: float
    growth: float | None = None
    metadata: dict | None = None


class AnalyticsMetric(BaseModel):
    """Analytics metric"""

    label: str
    value: float
    format: Literal["currency", "number", "percentage"]
    trend: float | None = None


class ExportRequest(BaseModel):
    """Export request schema"""

    format: Literal["csv", "excel"] = Field(default="csv")
    filters: AnalyticsFilter | None = None


class CustomQueryRequest(BaseModel):
    """Custom query request"""

    query: str = Field(..., min_length=1, max_length=1000)
    filters: AnalyticsFilter | None = None
