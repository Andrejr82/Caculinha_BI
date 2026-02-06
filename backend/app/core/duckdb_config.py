"""
DuckDB Configuration for Large Dataset Processing
Implements best practices for memory management and disk spilling
"""
import duckdb
import os
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DuckDBConfig:
    """
    DuckDB configuration manager for optimal memory handling
    """
    
    def __init__(self, memory_limit: str = "4GB", temp_dir: str = None):
        """
        Initialize DuckDB configuration
        
        Args:
            memory_limit: Maximum memory (e.g., '4GB', '8GB'). Default 4GB (50-70% of typical 8GB RAM)
            temp_dir: Temporary directory for disk spilling. If None, uses system temp
        """
        self.memory_limit = memory_limit
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "duckdb_spill")
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"DuckDB temp directory: {self.temp_dir}")
    
    def create_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Create a DuckDB connection with optimized settings for large datasets
        
        Returns:
            Configured DuckDB connection
        """
        conn = duckdb.connect(':memory:')
        
        # Memory Management
        conn.execute(f"SET memory_limit = '{self.memory_limit}'")
        conn.execute(f"SET temp_directory = '{self.temp_dir}'")
        
        # Performance Optimization
        conn.execute("SET threads TO 4")  # Adjust based on CPU cores
        conn.execute("SET preserve_insertion_order = false")  # Reduce memory for large imports
        
        # Enable disk spilling for larger-than-memory operations
        # This is enabled by default in DuckDB 0.10.0+, but we log it for clarity
        logger.info(f"DuckDB connection created with memory_limit={self.memory_limit}, temp_dir={self.temp_dir}")
        
        return conn
    
    def create_relation_from_arrow(self, conn: duckdb.DuckDBPyConnection, arrow_table):
        """
        Create a DuckDB relation from PyArrow table with zero-copy optimization
        
        Args:
            conn: DuckDB connection
            arrow_table: PyArrow Table
            
        Returns:
            DuckDB relation
        """
        # Zero-copy integration: DuckDB can directly query Arrow tables
        # without materializing them in memory
        return conn.from_arrow(arrow_table)


# Global singleton instance
_duckdb_config = None


def get_duckdb_config(memory_limit: str = "4GB", temp_dir: str = None) -> DuckDBConfig:
    """
    Get or create the global DuckDB configuration instance
    
    Args:
        memory_limit: Maximum memory limit
        temp_dir: Temporary directory for spilling
        
    Returns:
        DuckDB configuration instance
    """
    global _duckdb_config
    if _duckdb_config is None:
        _duckdb_config = DuckDBConfig(memory_limit=memory_limit, temp_dir=temp_dir)
    return _duckdb_config


def get_safe_connection() -> duckdb.DuckDBPyConnection:
    """
    Convenience function to get a configured DuckDB connection
    
    Returns:
        Configured DuckDB connection with memory limits and disk spilling
    """
    config = get_duckdb_config()
    return config.create_connection()
