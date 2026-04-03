"""API V1 router."""

from fastapi import APIRouter

from backend.app.api.router_setup import register_versioned_routes

api_router = APIRouter(prefix="/api/v1")
register_versioned_routes(api_router)
