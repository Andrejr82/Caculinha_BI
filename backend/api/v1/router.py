"""
API V1 Router — Agregador de Endpoints

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from fastapi import APIRouter

from backend.api.v1.endpoints.chat_v2 import router as chat_router
from backend.api.v1.endpoints.ingest import router as ingest_router
from backend.api.v1.endpoints.memory import router as memory_router
from backend.api.v1.endpoints.metrics import router as metrics_router
from backend.api.v1.endpoints.feedback import router as feedback_router
from backend.api.v1.endpoints.catalog import router as catalog_router
from backend.api.v1.endpoints.auth import router as auth_router

# Importar dashboard do V2 para disponibilizar no V1
from backend.api.v2.endpoints.dashboard import router as dashboard_router

# Importar analytics do app package (endpoints de KPIs, top-queries, etc.)
from backend.app.api.v1.endpoints.analytics import router as analytics_router

# Importar metrics do app package (business-kpis, real-time-kpis, etc.)
from backend.app.api.v1.endpoints.metrics import router as app_metrics_router

# ADMIN-ONLY routers
from backend.app.api.v1.endpoints.admin_dashboard import router as admin_dashboard_router
from backend.app.api.v1.endpoints.admin_evals import router as admin_evals_router

# Router principal v1
api_router = APIRouter(prefix="/api/v1")

# Inclui sub-routers
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(ingest_router)
api_router.include_router(memory_router)
api_router.include_router(metrics_router)
api_router.include_router(feedback_router)
api_router.include_router(catalog_router)
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(analytics_router)  # /api/v1/analytics/*
api_router.include_router(app_metrics_router)  # /api/v1/metrics/* (business-kpis)

# ADMIN-ONLY endpoints (require admin role or user@agentbi.com)
api_router.include_router(admin_dashboard_router)  # /api/v1/admin/dashboard/*
api_router.include_router(admin_evals_router)  # /api/v1/admin/evals/*

__all__ = ["api_router"]




