"""
API V1 Router
Combines all v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
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
    dashboard   # Dashboard endpoints (Forecasting, Executive, Suppliers)
)

api_router = APIRouter()

# Include all endpoint routers
# Health check endpoints (no auth required)
api_router.include_router(health.router)

# Authentication endpoints
api_router.include_router(auth.router)
api_router.include_router(auth_alt.router_alt)  # Login alternativo
api_router.include_router(analytics.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(metrics.router)  # Dashboard metrics
api_router.include_router(chat.router)  # BI Chat

# New Endpoints
api_router.include_router(rupturas.router)
api_router.include_router(transfers.router)
api_router.include_router(diagnostics.router)
api_router.include_router(learning.router)
api_router.include_router(playground.router)
api_router.include_router(shared.router)
api_router.include_router(preferences.router)
api_router.include_router(insights.router)
api_router.include_router(code_chat.router)  # Code Chat RAG

# Frontend Logs
api_router.include_router(frontend_logs.router)

# Dashboard endpoints (Forecasting, Executive, Suppliers)
api_router.include_router(dashboard.router)