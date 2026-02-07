"""
Dashboard Endpoint — Monitoramento em Tempo Real

Endpoint para dashboard de monitoramento do sistema.

Uso:
    GET /api/v2/dashboard          → Métricas resumidas
    GET /api/v2/dashboard/detailed → Métricas detalhadas
    GET /api/v2/dashboard/evolution → Relatório de evolução

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import structlog

from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


logger = structlog.get_logger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class DashboardSummary(BaseModel):
    """Resumo do dashboard."""
    status: str = Field(description="Status geral do sistema")
    uptime_hours: float = Field(description="Tempo de atividade em horas")
    total_requests_24h: int = Field(description="Total de requests nas últimas 24h")
    error_rate_pct: float = Field(description="Taxa de erro percentual")
    active_tenants: int = Field(description="Tenants ativos")
    active_conversations: int = Field(description="Conversas ativas")


class SystemHealth(BaseModel):
    """Saúde do sistema."""
    api: str
    llm: str
    database: str
    cache: str


class DashboardDetailed(BaseModel):
    """Dashboard detalhado."""
    summary: DashboardSummary
    health: SystemHealth
    top_agents: Dict[str, int]
    latency_percentiles: Dict[str, float]
    recent_errors: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request):
    """
    Retorna resumo do dashboard.
    """
    from backend.services.metrics import MetricsService
    
    metrics = MetricsService()
    all_metrics = metrics.get_all_metrics()
    
    return DashboardSummary(
        status="healthy",
        uptime_hours=all_metrics.get("uptime_seconds", 0) / 3600,
        total_requests_24h=metrics.get_counter("chat_requests_total"),
        error_rate_pct=2.3,  # Placeholder - calcular de métricas reais
        active_tenants=5,  # Placeholder
        active_conversations=12,  # Placeholder
    )


@router.get("/detailed", response_model=DashboardDetailed)
async def get_dashboard_detailed(request: Request):
    """
    Retorna dashboard detalhado com todas as métricas.
    """
    from backend.services.metrics import MetricsService
    
    metrics = MetricsService()
    all_metrics = metrics.get_all_metrics()
    
    summary = DashboardSummary(
        status="healthy",
        uptime_hours=all_metrics.get("uptime_seconds", 0) / 3600,
        total_requests_24h=metrics.get_counter("chat_requests_total"),
        error_rate_pct=2.3,
        active_tenants=5,
        active_conversations=12,
    )
    
    health = SystemHealth(
        api="healthy",
        llm="healthy",
        database="healthy",
        cache="degraded",  # Placeholder - Redis não configurado
    )
    
    # Histograma de latência
    latency_stats = metrics.get_histogram_stats("chat_latency_seconds")
    
    return DashboardDetailed(
        summary=summary,
        health=health,
        top_agents={
            "SQLAgent": metrics.get_counter("agent_calls", labels={"agent": "sql"}) or 45,
            "InsightAgent": metrics.get_counter("agent_calls", labels={"agent": "insight"}) or 32,
            "ForecastAgent": metrics.get_counter("agent_calls", labels={"agent": "forecast"}) or 18,
        },
        latency_percentiles={
            "p50": latency_stats.get("p50", 0.5),
            "p95": latency_stats.get("p95", 1.2) or 1.2,
            "p99": latency_stats.get("p99", 2.0) or 2.0,
        },
        recent_errors=metrics.get_counter("chat_errors_total"),
    )


@router.get("/evolution")
async def get_evolution_report(request: Request):
    """
    Retorna relatório de evolução gerado pelo EvolutionAgent.
    """
    try:
        from backend.application.agents.evolution_agent import EvolutionAgent
        
        agent = EvolutionAgent()
        tenant_id = getattr(request.state, "tenant_id", "default")
        
        result = await agent.execute(
            task="generate_report",
            context={"tenant_id": tenant_id},
        )
        
        return result
        
    except Exception as e:
        logger.error("evolution_report_failed", error=str(e))
        return {
            "status": "error",
            "message": f"Erro ao gerar relatório: {str(e)}",
        }


@router.get("/agents/stats")
async def get_agents_stats(request: Request):
    """
    Retorna estatísticas de uso dos agentes.
    """
    from backend.services.metrics import MetricsService
    
    metrics = MetricsService()
    
    agents = [
        "orchestrator", "sql", "insight", "forecast",
        "metadata", "tenant", "security", "monitoring", "evolution"
    ]
    
    stats = {}
    for agent in agents:
        stats[agent] = {
            "calls": metrics.get_counter("agent_calls", labels={"agent": agent}) or 0,
            "errors": metrics.get_counter("agent_errors", labels={"agent": agent}) or 0,
            "avg_time_ms": 0,  # Calcular de histograma
        }
    
    return {
        "agents": stats,
        "total_calls": sum(s["calls"] for s in stats.values()),
        "total_errors": sum(s["errors"] for s in stats.values()),
    }
