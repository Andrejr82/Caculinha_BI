"""
API V1 Router — Agregador de Endpoints

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from fastapi import APIRouter

from backend.api.v1.endpoints.chat_v2 import router as chat_router
from backend.api.v1.endpoints.ingest import router as ingest_router
from backend.api.v1.endpoints.memory import router as memory_router

# Router principal v1
api_router = APIRouter(prefix="/api/v1")

# Inclui sub-routers
api_router.include_router(chat_router)
api_router.include_router(ingest_router)
api_router.include_router(memory_router)

__all__ = ["api_router"]
