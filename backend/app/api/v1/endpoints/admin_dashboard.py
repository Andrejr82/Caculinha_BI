"""
Admin Dashboard Endpoints - ADMIN ONLY
Platform health, traffic, usage, and quality metrics.

All endpoints require admin role or user@agentbi.com email.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Any, List
import os
import time
import logging
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.dependencies import require_admin
from backend.app.infrastructure.database.models import User
from backend.app.config.settings import settings

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])
logger = logging.getLogger(__name__)

# Track server start time
SERVER_START_TIME = time.time()


# ==================== Response Models ====================

class HealthResponse(BaseModel):
    """Platform health status."""
    status: str
    environment: str
    version: str
    uptime_seconds: int
    uptime_formatted: str
    python_version: str
    
class TrafficMetrics(BaseModel):
    """Traffic and performance metrics."""
    total_requests: int
    requests_per_minute: float
    error_count: int
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

class UsageMetrics(BaseModel):
    """Platform usage metrics."""
    active_users_24h: int
    total_queries_today: int
    top_endpoints: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]

class QualityMetrics(BaseModel):
    """Response quality metrics."""
    total_evaluations: int
    average_score: float
    high_score_count: int
    low_score_count: int
    low_score_rate: float
    score_distribution: Dict[str, int]


class ChatSLOMetrics(BaseModel):
    """SLO operacional específico do ChatBI."""
    total_requests: int
    error_rate_pct: float
    p95_latency_ms: float
    p95_simple_ms: float
    p95_complex_ms: float
    cache_hit_rate_pct: float
    tool_calls_total: int
    avg_tools_per_request: float
    tokens_in_total: int
    tokens_out_total: int
    estimated_cost_usd: float
    feedback_useful_rate_pct: float
    slo_status: str


def _pctl_or_fallback(stats: Dict[str, Any]) -> float:
    p95 = stats.get("p95")
    if isinstance(p95, (int, float)):
        return float(p95)
    p50 = stats.get("p50")
    if isinstance(p50, (int, float)):
        return float(p50)
    avg = stats.get("avg")
    if isinstance(avg, (int, float)):
        return float(avg)
    return 0.0


# ==================== Endpoints ====================

@router.get("/health", response_model=HealthResponse)
async def get_platform_health(
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Get platform health status.
    
    Returns environment, version, uptime, and system info.
    ADMIN ONLY.
    """
    import sys
    
    uptime = int(time.time() - SERVER_START_TIME)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development"),
        version=os.getenv("APP_VERSION", "2.0.0"),
        uptime_seconds=uptime,
        uptime_formatted=uptime_str,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


@router.get("/traffic", response_model=TrafficMetrics)
async def get_traffic_metrics(
    current_user: Annotated[User, Depends(require_admin)],
    hours: int = 24
):
    """
    Get traffic and performance metrics.
    
    Returns request count, latencies, and error rates.
    ADMIN ONLY.
    """
    try:
        from backend.services.metrics import MetricsService
        metrics = MetricsService()
        
        # Use public getter methods (not private attributes)
        total_requests = metrics.get_counter("chat_requests_total")
        error_count = metrics.get_counter("chat_errors_total")
        auth_logins = metrics.get_counter("auth_logins_total")
        
        # Calculate rates
        uptime_hours = max((time.time() - SERVER_START_TIME) / 3600, 0.1)
        requests_per_minute = total_requests / (uptime_hours * 60) if uptime_hours > 0 else 0
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        # Get latency percentiles from histogram
        latency_stats = metrics.get_histogram_stats("chat_latency_seconds")
        p50 = latency_stats.get("p50", 0) or 0
        p95 = latency_stats.get("p95", 0) or p50
        p99 = latency_stats.get("p99", 0) or p95
        
        return TrafficMetrics(
            total_requests=total_requests + auth_logins,  # Include auth requests
            requests_per_minute=round(requests_per_minute, 2),
            error_count=error_count,
            error_rate=round(error_rate, 2),
            p50_latency_ms=round(p50 * 1000, 2),
            p95_latency_ms=round(p95 * 1000, 2),
            p99_latency_ms=round(p99 * 1000, 2)
        )
    except Exception as e:
        logger.error(f"Error getting traffic metrics: {e}")
        return TrafficMetrics(
            total_requests=0,
            requests_per_minute=0,
            error_count=0,
            error_rate=0,
            p50_latency_ms=0,
            p95_latency_ms=0,
            p99_latency_ms=0
        )


@router.get("/usage", response_model=UsageMetrics)
async def get_usage_metrics(
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Get platform usage metrics.
    
    Returns active users, query counts, and top endpoints.
    ADMIN ONLY.
    """
    try:
        from backend.services.metrics import MetricsService
        metrics = MetricsService()
        
        # Get all metrics using public API
        all_metrics = metrics.get_all_metrics()
        counters = all_metrics.get("counters", {})
        
        # Extract endpoint-level counters
        top_endpoints = []
        for key, value in counters.items():
            if not key.startswith("__"):
                top_endpoints.append({"endpoint": key, "count": value})
        
        top_endpoints = sorted(top_endpoints, key=lambda x: x["count"], reverse=True)[:10]
        
        # Calculate totals
        total_requests = sum(counters.values())
        
        return UsageMetrics(
            active_users_24h=metrics.get_counter("auth_logins_total"),
            total_queries_today=total_requests,
            top_endpoints=top_endpoints,
            top_users=[]  # User-level tracking not implemented yet
        )
    except Exception as e:
        logger.error(f"Error getting usage metrics: {e}")
        return UsageMetrics(
            active_users_24h=0,
            total_queries_today=0,
            top_endpoints=[],
            top_users=[]
        )


@router.get("/chat-slo", response_model=ChatSLOMetrics)
async def get_chat_slo_metrics(
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Dashboard operacional consolidado do ChatBI para SLO/SLA.
    """
    from backend.services.metrics import MetricsService

    metrics = MetricsService()
    total_requests = metrics.get_counter("chat_requests_total")
    total_errors = metrics.get_counter("chat_errors_total")
    total_tool_calls = metrics.get_counter("chat_tool_calls_total")
    tokens_in = metrics.get_counter("chat_tokens_in_total")
    tokens_out = metrics.get_counter("chat_tokens_out_total")
    cache_lookups = metrics.get_counter("chat_cache_lookups_total")
    cache_hits = metrics.get_counter("chat_cache_hits_total")

    latency = metrics.get_histogram_stats("chat_latency_seconds")
    latency_simple = metrics.get_histogram_stats("chat_latency_seconds", labels={"complexity": "simple"})
    latency_complex = metrics.get_histogram_stats("chat_latency_seconds", labels={"complexity": "complex"})

    p95_latency_ms = _pctl_or_fallback(latency) * 1000
    p95_simple_ms = _pctl_or_fallback(latency_simple) * 1000
    p95_complex_ms = _pctl_or_fallback(latency_complex) * 1000
    error_rate_pct = (total_errors / total_requests * 100.0) if total_requests > 0 else 0.0
    cache_hit_rate_pct = (cache_hits / cache_lookups * 100.0) if cache_lookups > 0 else 0.0
    avg_tools_per_request = (total_tool_calls / total_requests) if total_requests > 0 else 0.0

    # Estimativa de custo via parâmetros configuráveis (default 0.0 no ambiente).
    input_cost_per_1k = float(getattr(settings, "OBS_COST_USD_PER_1K_INPUT_TOKENS", 0.0) or 0.0)
    output_cost_per_1k = float(getattr(settings, "OBS_COST_USD_PER_1K_OUTPUT_TOKENS", 0.0) or 0.0)
    estimated_cost_usd = ((tokens_in / 1000.0) * input_cost_per_1k) + ((tokens_out / 1000.0) * output_cost_per_1k)

    # Feedback útil (positivo) para visão de qualidade percebida.
    feedback_useful_rate_pct = 0.0
    try:
        feedback_path = Path(settings.LEARNING_FEEDBACK_PATH) / "feedback.jsonl"
        if feedback_path.exists():
            total_feedback = 0
            useful_feedback = 0
            with open(feedback_path, "r", encoding="utf-8") as f:
                for line in f:
                    raw = (line or "").strip()
                    if not raw:
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    total_feedback += 1
                    if str(item.get("feedback_type", "")).lower() == "positive":
                        useful_feedback += 1
            if total_feedback > 0:
                feedback_useful_rate_pct = (useful_feedback / total_feedback) * 100.0
    except Exception as e:
        logger.warning("chat_slo_feedback_read_failed: %s", e)

    # SLO padrão da Fase 2 (documento de produção enterprise)
    slo_simple_ok = p95_simple_ms <= 3000.0 if p95_simple_ms > 0 else True
    slo_complex_ok = p95_complex_ms <= 8000.0 if p95_complex_ms > 0 else True
    slo_error_ok = error_rate_pct <= 1.0
    slo_status = "healthy" if (slo_simple_ok and slo_complex_ok and slo_error_ok) else "degraded"

    return ChatSLOMetrics(
        total_requests=total_requests,
        error_rate_pct=round(error_rate_pct, 2),
        p95_latency_ms=round(p95_latency_ms, 2),
        p95_simple_ms=round(p95_simple_ms, 2),
        p95_complex_ms=round(p95_complex_ms, 2),
        cache_hit_rate_pct=round(cache_hit_rate_pct, 2),
        tool_calls_total=total_tool_calls,
        avg_tools_per_request=round(avg_tools_per_request, 3),
        tokens_in_total=tokens_in,
        tokens_out_total=tokens_out,
        estimated_cost_usd=round(estimated_cost_usd, 6),
        feedback_useful_rate_pct=round(feedback_useful_rate_pct, 2),
        slo_status=slo_status,
    )


@router.get("/quality", response_model=QualityMetrics)
async def get_quality_metrics(
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Get response quality metrics.
    
    Returns average scores, distribution, and low-score alerts.
    ADMIN ONLY.
    """
    try:
        from backend.app.core.evaluations_repository import evaluations_repo
        
        evals = evaluations_repo.get_all(limit=1000)
        
        if not evals:
            return QualityMetrics(
                total_evaluations=0,
                average_score=0,
                high_score_count=0,
                low_score_count=0,
                low_score_rate=0,
                score_distribution={"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
            )
        
        scores = [e.get("overall_score", 0) for e in evals]
        avg_score = sum(scores) / len(scores)
        high_count = sum(1 for s in scores if s >= 70)
        low_count = sum(1 for s in scores if s < 50)
        
        # Score distribution
        distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for s in scores:
            if s <= 20: distribution["0-20"] += 1
            elif s <= 40: distribution["21-40"] += 1
            elif s <= 60: distribution["41-60"] += 1
            elif s <= 80: distribution["61-80"] += 1
            else: distribution["81-100"] += 1
        
        return QualityMetrics(
            total_evaluations=len(evals),
            average_score=round(avg_score, 1),
            high_score_count=high_count,
            low_score_count=low_count,
            low_score_rate=round(low_count / len(evals) * 100, 1),
            score_distribution=distribution
        )
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        return QualityMetrics(
            total_evaluations=0,
            average_score=0,
            high_score_count=0,
            low_score_count=0,
            low_score_rate=0,
            score_distribution={"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        )
