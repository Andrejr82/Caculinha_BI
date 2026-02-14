"""
API V2 - Alias Layer for V1
Redirects all /api/v2 calls to /api/v1 logic to maintain compatibility.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import feedback as legacy_feedback

# Import canonical routers from v1
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
    code_chat,
    dashboard,
    catalog,
    ingest,
    memory,
)

router = APIRouter()

# Re-include ALL v1 routers but under the v2 prefix (managed in main.py)
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_alt.router_alt, tags=["Auth"])
router.include_router(analytics.router, tags=["Analytics"])
router.include_router(reports.router, tags=["Reports"])
router.include_router(admin.router, tags=["Admin"])
router.include_router(admin_dashboard.router, tags=["Admin Dashboard"])
router.include_router(admin_evals.router, tags=["Admin Evaluations"])
router.include_router(metrics.router, tags=["Metrics"])
router.include_router(chat.router, tags=["Chat"])
router.include_router(rupturas.router, tags=["Rupturas"])
router.include_router(transfers.router, tags=["Transfers"])
router.include_router(diagnostics.router, tags=["Diagnostics"])
router.include_router(learning.router, tags=["Learning"])
router.include_router(playground.router, tags=["Playground"])
router.include_router(shared.router, tags=["Shared"])
router.include_router(preferences.router, tags=["Preferences"])
router.include_router(insights.router, tags=["Insights"])
router.include_router(code_chat.router, tags=["CodeChat"])
router.include_router(dashboard.router, tags=["Dashboard"])

# Legacy/Extra Endpoints
router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
router.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
router.include_router(memory.router, prefix="/memory", tags=["Memory"])
router.include_router(legacy_feedback.router, tags=["Feedback"])
