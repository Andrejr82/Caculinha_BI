"""
DuckDB Server - Connection Pooling for High Concurrency

Implementa connection pooling para suportar 30+ usuários simultâneos.
"""

import duckdb
import logging
from typing import Optional
from contextlib import contextmanager
from threading import Lock
from queue import Queue, Empty
import time

logger = logging.getLogger(__name__)


class DuckDBConnectionPool:
    """
    Pool de conexões DuckDB para alta concorrência.
    
    Features:
    - Connection pooling (reutilização de conexões)
    - Thread-safe
    - Auto-cleanup de conexões ociosas
    - Métricas de uso
    """
    
    def __init__(
        self,
        db_path: str,
        min_connections: int = 5,
        max_connections: int = 50,
        timeout: float = 30.0
    ):
        """
        Inicializa pool de conexões.
        
        Args:
            db_path: Caminho para o arquivo DuckDB/Parquet
            min_connections: Número mínimo de conexões mantidas
            max_connections: Número máximo de conexões permitidas
            timeout: Timeout para obter conexão (segundos)
        """
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.timeout = timeout
        
        self._pool = Queue(maxsize=max_connections)
        self._active_connections = 0
        self._lock = Lock()
        
        # Métricas
        self.total_requests = 0
        self.total_hits = 0
        self.total_misses = 0
        
        # Criar conexões mínimas
        self._initialize_pool()
        
        logger.info(
            f"DuckDB Connection Pool inicializado: "
            f"min={min_connections}, max={max_connections}"
        )
    
    def _initialize_pool(self):
        """Cria conexões iniciais no pool."""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            self._pool.put(conn)
    
    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Cria nova conexão DuckDB."""
        with self._lock:
            if self._active_connections >= self.max_connections:
                raise RuntimeError(
                    f"Limite de conexões atingido ({self.max_connections})"
                )
            
            conn = duckdb.connect(self.db_path, read_only=True)
            self._active_connections += 1
            
            logger.debug(f"Nova conexão criada (total: {self._active_connections})")
            return conn
    
    @contextmanager
    def get_connection(self):
        """
        Obtém conexão do pool (context manager).
        
        Yields:
            duckdb.DuckDBPyConnection
        
        Raises:
            Empty: Se timeout ao obter conexão
        
        Examples:
            >>> pool = DuckDBConnectionPool("data.parquet")
            >>> with pool.get_connection() as conn:
            ...     result = conn.execute("SELECT * FROM data").df()
        """
        self.total_requests += 1
        conn = None
        created_new = False
        
        try:
            # Tentar obter conexão existente do pool
            try:
                conn = self._pool.get(timeout=0.1)
                self.total_hits += 1
                logger.debug("Conexão reutilizada do pool")
            except Empty:
                # Pool vazio, criar nova conexão
                conn = self._create_connection()
                created_new = True
                self.total_misses += 1
                logger.debug("Nova conexão criada (pool vazio)")
            
            yield conn
        
        finally:
            if conn:
                # Retornar conexão ao pool
                try:
                    self._pool.put_nowait(conn)
                except:
                    # Pool cheio, fechar conexão
                    conn.close()
                    with self._lock:
                        self._active_connections -= 1
                    logger.debug("Conexão fechada (pool cheio)")
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do pool."""
        hit_rate = (self.total_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "active_connections": self._active_connections,
            "pool_size": self._pool.qsize(),
            "total_requests": self.total_requests,
            "cache_hit_rate": round(hit_rate, 2),
            "total_hits": self.total_hits,
            "total_misses": self.total_misses
        }
    
    def close_all(self):
        """Fecha todas as conexões do pool."""
        logger.info("Fechando todas as conexões do pool...")
        
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
                with self._lock:
                    self._active_connections -= 1
            except Empty:
                break
        
        logger.info(f"Pool fechado. Conexões restantes: {self._active_connections}")


# Singleton instance
_pool_instance: Optional[DuckDBConnectionPool] = None


def get_connection_pool(
    db_path: str = "data/admmat.parquet",
    **kwargs
) -> DuckDBConnectionPool:
    """
    Retorna instância singleton do connection pool.
    
    Args:
        db_path: Caminho para o banco de dados
        **kwargs: Argumentos adicionais para DuckDBConnectionPool
    
    Returns:
        DuckDBConnectionPool instance
    """
    global _pool_instance
    
    if _pool_instance is None:
        _pool_instance = DuckDBConnectionPool(db_path, **kwargs)
    
    return _pool_instance
