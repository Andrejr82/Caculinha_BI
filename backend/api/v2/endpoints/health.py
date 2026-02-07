"""
Health Endpoint

Endpoints de verificação de saúde do sistema.

Uso:
    GET /api/v2/health
    GET /api/v2/health/detailed

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import structlog


logger = structlog.get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str
    timestamp: str
    version: str = "2.0.0"


class DetailedHealthResponse(BaseModel):
    """Resposta detalhada do health check."""
    status: str
    timestamp: str
    version: str
    components: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check básico.
    
    Returns:
        Status de saúde do sistema
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Health check detalhado com status de todos os componentes.
    
    Returns:
        Status detalhado de cada componente
    """
    from backend.infrastructure.adapters.data import DuckDBAdapter
    
    components = {}
    overall_healthy = True
    
    # Verificar DuckDB
    try:
        adapter = DuckDBAdapter()
        duckdb_healthy = await adapter.health_check()
        components["duckdb"] = {
            "status": "healthy" if duckdb_healthy else "unhealthy",
            "tables": await adapter.get_tables(),
        }
        adapter.close()
    except Exception as e:
        components["duckdb"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Verificar LLM (Gemini)
    try:
        import os
        api_key = os.getenv("GOOGLE_API_KEY")
        components["llm"] = {
            "status": "healthy" if api_key else "not_configured",
            "provider": "google",
            "model": os.getenv("LLM_MODEL_NAME", "gemini-2.5-pro"),
        }
    except Exception as e:
        components["llm"] = {"status": "unhealthy", "error": str(e)}
    
    return DetailedHealthResponse(
        status="healthy" if overall_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version="2.0.0",
        components=components,
    )
