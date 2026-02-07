"""
Vector Adapters — Inicialização

Este módulo contém os adapters de busca vetorial.

Uso:
    from backend.infrastructure.adapters.vector import DuckDBVectorAdapter

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from backend.infrastructure.adapters.vector.duckdb_vector_adapter import DuckDBVectorAdapter

__all__ = [
    "DuckDBVectorAdapter",
]
