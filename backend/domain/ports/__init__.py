"""
Domain Ports — Exportação de Interfaces

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from backend.domain.ports.memory_repository_port import IMemoryRepository
from backend.domain.ports.vector_repository_port import IVectorRepository
from backend.domain.ports.ranking_port import IRankingPort, RankedDocument
from backend.domain.ports.compression_port import ICompressionPort, CompressedContext
from backend.domain.ports.feature_store_port import IFeatureStore


__all__ = [
    # Ports
    "IMemoryRepository",
    "IVectorRepository",
    "IRankingPort",
    "ICompressionPort",
    "IFeatureStore",
    # Data Classes
    "RankedDocument",
    "CompressedContext",
]
