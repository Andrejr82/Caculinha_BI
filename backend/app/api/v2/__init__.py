"""API V2 alias layer for the active V1 surface."""

from fastapi import APIRouter

from backend.app.api.router_setup import register_versioned_routes

router = APIRouter()
register_versioned_routes(router, annotate_tags=True)
