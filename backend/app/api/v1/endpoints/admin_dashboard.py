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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.dependencies import require_admin
from backend.app.infrastructure.database.models import User

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
        
        # Get metrics from the last N hours
        total_requests = metrics._request_count
        error_count = metrics._error_count
        
        # Calculate rates
        uptime_hours = max((time.time() - SERVER_START_TIME) / 3600, 0.1)
        requests_per_minute = total_requests / (uptime_hours * 60) if uptime_hours > 0 else 0
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        # Get latency percentiles
        latencies = metrics._latency_samples if hasattr(metrics, '_latency_samples') else []
        p50 = sorted(latencies)[int(len(latencies) * 0.5)] if latencies else 0
        p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else p50
        p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 100 else p95
        
        return TrafficMetrics(
            total_requests=total_requests,
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
        
        # Get endpoint stats
        endpoint_stats = getattr(metrics, '_endpoint_stats', {})
        top_endpoints = [
            {"endpoint": k, "count": v}
            for k, v in sorted(endpoint_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Get user stats
        user_stats = getattr(metrics, '_user_stats', {})
        top_users = [
            {"user": k, "requests": v}
            for k, v in sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return UsageMetrics(
            active_users_24h=len(user_stats),
            total_queries_today=sum(endpoint_stats.values()),
            top_endpoints=top_endpoints,
            top_users=top_users
        )
    except Exception as e:
        logger.error(f"Error getting usage metrics: {e}")
        return UsageMetrics(
            active_users_24h=0,
            total_queries_today=0,
            top_endpoints=[],
            top_users=[]
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
