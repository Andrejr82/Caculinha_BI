"""
Memory Adapters — Inicialização

Este módulo contém os adapters de memória.

Uso:
    from backend.infrastructure.adapters.memory import (
        RedisMemoryAdapter,
        SQLiteMemoryAdapter,
    )

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from backend.infrastructure.adapters.memory.redis_memory_adapter import RedisMemoryAdapter
from backend.infrastructure.adapters.memory.sqlite_memory_adapter import SQLiteMemoryAdapter

__all__ = [
    "RedisMemoryAdapter",
    "SQLiteMemoryAdapter",
]
