"""
API V2 - Router Principal

Router principal da versão 2 da API com arquitetura Clean Architecture.

Uso:
    from backend.api.v2 import router
    app.include_router(router, prefix="/api/v2")

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from fastapi import APIRouter

from backend.api.v2.endpoints.chat import router as chat_router
from backend.api.v2.endpoints.health import router as health_router
from backend.api.v2.endpoints.agents import router as agents_router
from backend.api.v2.endpoints.auth import router as auth_router
from backend.api.v2.endpoints.metrics import router as metrics_router
from backend.api.v2.endpoints.dashboard import router as dashboard_router

router = APIRouter()

# Incluir routers
router.include_router(health_router, tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(agents_router, prefix="/agents", tags=["Agents"])
router.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
