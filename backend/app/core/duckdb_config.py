"""
DuckDB Configuration for Large Dataset Processing
Implements best practices for memory management and disk spilling
Otimizado para ambientes com pouca memória (Docker/WSL)
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
    
    def __init__(self, memory_limit: str = None, temp_dir: str = None):
        """
        Initialize DuckDB configuration
        
        Args:
            memory_limit: Maximum memory (e.g., '1GB', '2GB'). 
                          Default: Pega de DUCKDB_MEMORY_LIMIT ou usa 1GB
            temp_dir: Temporary directory for disk spilling. If None, uses system temp
        """
        # Pega o limite do docker-compose ou usa um padrão seguro (1GB)
        self.memory_limit = memory_limit or os.getenv("DUCKDB_MEMORY_LIMIT", "1GB")
        self.threads = int(os.getenv("DUCKDB_THREADS", "2"))
        
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "duckdb_spill")
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"DuckDB Config: memory={self.memory_limit}, threads={self.threads}, spill={self.temp_dir}")
    
    def create_connection(self, database: str = ':memory:') -> duckdb.DuckDBPyConnection:
        """
        Create a DuckDB connection with optimized settings for large datasets
        
        Returns:
            Configured DuckDB connection
        """
        conn = duckdb.connect(database=database)
        
        # Comandos PRAGMA essenciais para pouca memória
        # Memory Management
        conn.execute(f"SET memory_limit = '{self.memory_limit}'")
        conn.execute(f"SET temp_directory = '{self.temp_dir}'")
        
        # Performance Optimization (Otimizado via env)
        conn.execute(f"SET threads = {self.threads}") 
        conn.execute("SET preserve_insertion_order = false")  # Economiza RAM significativamente
        
        logger.info(f"DuckDB connection established (memory_limit={self.memory_limit})")
        
        return conn


# Global singleton instance
_duckdb_config = None


def get_duckdb_config(memory_limit: str = None, temp_dir: str = None) -> DuckDBConfig:
    """Get the global DuckDB configuration instance"""
    global _duckdb_config
    if _duckdb_config is None:
        _duckdb_config = DuckDBConfig(memory_limit=memory_limit, temp_dir=temp_dir)
    return _duckdb_config


def get_safe_connection() -> duckdb.DuckDBPyConnection:
    """Get a configured DuckDB connection (Singleton)"""
    config = get_duckdb_config()
    return config.create_connection()


# Alias para compatibilidade com o pedido do usuário
def get_db_connection() -> duckdb.DuckDBPyConnection:
    """Alias para get_safe_connection para compatibilidade interna"""
    return get_safe_connection()
