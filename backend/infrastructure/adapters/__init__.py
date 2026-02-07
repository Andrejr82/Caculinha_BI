"""
Infrastructure Adapters — Exportação de Adapters

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from backend.infrastructure.adapters.redis_memory_adapter import RedisMemoryAdapter
from backend.infrastructure.adapters.sqlite_memory_adapter import SQLiteMemoryAdapter
from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter
from backend.infrastructure.adapters.bm25_ranking_adapter import BM25RankingAdapter
from backend.infrastructure.adapters.llm_compression_adapter import LLMCompressionAdapter
from backend.infrastructure.adapters.duckdb_feature_store_adapter import DuckDBFeatureStoreAdapter


__all__ = [
    "RedisMemoryAdapter",
    "SQLiteMemoryAdapter",
    "DuckDBVectorAdapter",
    "BM25RankingAdapter",
    "LLMCompressionAdapter",
    "DuckDBFeatureStoreAdapter",
]
