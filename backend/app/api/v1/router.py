"""
API V1 Router
Combines all v1 endpoints
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import feedback as legacy_feedback

from backend.app.api.v1.endpoints import (
    admin,
    admin_dashboard,
    admin_evals,
    analytics,
    auth,
    reports,
    auth_alt,
    metrics,
    chat,
    rupturas,
    transfers,
    diagnostics,
    learning,
    playground,
    frontend_logs,
    shared,
    preferences,
    insights,
    health,
    code_chat,  # Code Chat RAG
    dashboard,   # Dashboard endpoints (Forecasting, Executive, Suppliers)
    catalog,
    ingest,
    memory,
)

api_router = APIRouter(prefix="/api/v1")

# Include all module routers
api_router.include_router(health.router)

# Authentication endpoints
api_router.include_router(auth.router)
api_router.include_router(auth_alt.router_alt) # Backup auth
api_router.include_router(analytics.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_evals.router)
api_router.include_router(metrics.router)
api_router.include_router(chat.router)

# New Endpoints
api_router.include_router(rupturas.router)
api_router.include_router(transfers.router)
api_router.include_router(diagnostics.router)
api_router.include_router(learning.router)
api_router.include_router(playground.router)
api_router.include_router(shared.router)
api_router.include_router(preferences.router)
api_router.include_router(insights.router)
api_router.include_router(code_chat.router)

# Frontend Logs
api_router.include_router(frontend_logs.router)

# Dashboard endpoints (Forecasting, Executive, Suppliers)
api_router.include_router(dashboard.router)

# Special non-prefixed or differently-prefixed routers
api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
api_router.include_router(memory.router, prefix="/memory", tags=["Memory"])
api_router.include_router(legacy_feedback.router, tags=["Feedback"])
