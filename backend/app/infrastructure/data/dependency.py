"""
Data Adapter Dependency
Provides the DuckDBEnhancedAdapter instance to API endpoints.
"""

from typing import Annotated
from fastapi import Depends, Request

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter, DuckDBEnhancedAdapter

def get_data_adapter(request: Request) -> DuckDBEnhancedAdapter:
    """
    Dependency to get the DuckDBEnhancedAdapter instance.
    Uses singleton pattern from get_duckdb_adapter().
    """
    return get_duckdb_adapter()

# Type alias for easier usage in endpoints
DataAdapter = Annotated[DuckDBEnhancedAdapter, Depends(get_data_adapter)]
