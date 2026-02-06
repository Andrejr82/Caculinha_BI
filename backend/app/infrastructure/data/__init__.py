"""
Infrastructure Data Module
"""

from .duckdb_pool import DuckDBConnectionPool, get_connection_pool

__all__ = [
    'DuckDBConnectionPool',
    'get_connection_pool'
]
