"""
Shared API router registration for versioned aliases.
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    admin,
    admin_dashboard,
    admin_evals,
    analytics,
    auth,
    basket_analysis,
    catalog,
    chat,
    competitive,
    dashboard,
    diagnostics,
    feedback,
    frontend_logs,
    health,
    ingest,
    insights,
    learning,
    memory,
    metrics,
    playground,
    preferences,
    reports,
    rupturas,
    shared,
    transfers,
)


def register_versioned_routes(router: APIRouter, annotate_tags: bool = False) -> APIRouter:
    """
    Attach the active v1 endpoint set to a router instance.

    When ``annotate_tags`` is true, explicit tags are applied to keep the alias
    layer documentation grouped without maintaining a second router list.
    """

    def include(module_router, *, tags=None, prefix=None):
        kwargs = {}
        if annotate_tags and tags:
            kwargs["tags"] = tags
        if prefix is not None:
            kwargs["prefix"] = prefix
        router.include_router(module_router, **kwargs)

    include(health.router, tags=["Health"])
    include(auth.router, tags=["Auth"])
    include(analytics.router, tags=["Analytics"])
    include(basket_analysis.router, tags=["Analytics"])
    include(reports.router, tags=["Reports"])
    include(admin.router, tags=["Admin"])
    include(admin_dashboard.router, tags=["Admin Dashboard"])
    include(admin_evals.router, tags=["Admin Evaluations"])
    include(metrics.router, tags=["Metrics"])
    include(chat.router, tags=["Chat"])
    include(rupturas.router, tags=["Rupturas"])
    include(transfers.router, tags=["Transfers"])
    include(diagnostics.router, tags=["Diagnostics"])
    include(learning.router, tags=["Learning"])
    include(playground.router, tags=["Playground"])
    include(shared.router, tags=["Shared"])
    include(preferences.router, tags=["Preferences"])
    include(insights.router, tags=["Insights"])
    include(frontend_logs.router, tags=["Logs"])
    include(dashboard.router, tags=["Dashboard"])
    include(catalog.router, prefix="/catalog", tags=["Catalog"])
    include(ingest.router, tags=["Ingest"])
    include(memory.router, tags=["Memory"])
    include(competitive.router, tags=["Competitive"])
    include(feedback.router, tags=["Feedback"])
    return router
