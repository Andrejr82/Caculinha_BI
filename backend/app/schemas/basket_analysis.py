from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class BasketAnalysisRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    une: str | None = None
    segment: str | None = None
    category: str | None = None
    target_product: str | None = None
    min_support: float = Field(default=0.01, ge=0.0001, le=1.0)
    min_confidence: float = Field(default=0.2, ge=0.0, le=1.0)
    min_lift: float = Field(default=1.0, ge=0.0, le=100.0)
    max_rules: int = Field(default=20, ge=1, le=100)


class BasketItemsetResult(BaseModel):
    items: list[str]
    support: float
    size: int


class BasketRuleResult(BaseModel):
    antecedent: list[str]
    consequent: list[str]
    support: float
    confidence: float
    lift: float


class BasketAnalysisResponse(BaseModel):
    status: Literal["success", "unsupported", "no_data", "error"]
    analysis_mode: Literal["real_transactional", "subset_transactional_supported", "unsupported"]
    data_source: str
    transactions_analyzed: int
    unique_items: int
    parameters: dict[str, Any]
    top_itemsets: list[BasketItemsetResult]
    top_rules: list[BasketRuleResult]
    business_summary: list[str]
    limitations: list[str]
    diagnostics: dict[str, Any]
