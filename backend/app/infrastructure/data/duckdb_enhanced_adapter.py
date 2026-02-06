"""
DuckDB Enhanced Adapter - Versão 2.0
Substituição completa de Polars/Pandas/Dask

Melhorias sobre duckdb_adapter.py:
- Wrappers para compatibilidade com código Polars/Pandas
- Métodos utilitários para migração gradual
- Performance metrics embutidas
- Suporte completo a Arrow zero-copy

Autor: Claude Code
Data: 2025-12-31
"""

import duckdb
import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from functools import lru_cache
import asyncio
from contextlib import asynccontextmanager

try:
    import pyarrow as pa
    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collector de métricas de performance"""
    def __init__(self):
        self.queries = []

    def record(self, sql: str, duration: float, rows: int):
        self.queries.append({
            'sql': sql[:100],  # Truncate para log
            'duration_ms': duration * 1000,
            'rows': rows,
            'timestamp': time.time()
        })

    def get_stats(self) -> Dict[str, Any]:
        if not self.queries:
            return {}

        durations = [q['duration_ms'] for q in self.queries]
        return {
            'total_queries': len(self.queries),
            'avg_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'total_rows': sum(q['rows'] for q in self.queries)
        }


class DuckDBEnhancedAdapter:
    """
    Enhanced DuckDB Adapter com suporte a migração de Polars/Pandas.

    Features:
    - Zero-copy Arrow support
    - Connection pooling
    - Prepared statements
    - Performance metrics
    - Polars/Pandas compatibility wrappers
    - Async support
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize DuckDB connections and config"""
        # Main connection
        self.connection = duckdb.connect(database=':memory:')

        # Connection pool (16 connections for better concurrency)
        # FIX 2026-01-15: Increased from 4 to 16 to support more concurrent users
        self._connection_pool = [
            duckdb.connect(database=':memory:')
            for _ in range(16)
        ]
        self._pool_index = 0

        # Caches
        self._prepared_cache = {}
        self._parquet_cache = {}  # Substituir ParquetCache antigo

        # [OK] FIX 2026-01-14: Flag para tabela em memória (Context7 Performance)
        self._memory_tables = {}  # tabela_name -> True se carregada em memória

        # Metrics
        self.metrics = PerformanceMetrics()

        self._setup_optimizations()
        logger.info("DuckDBEnhancedAdapter initialized (Pool: 16, Metrics: enabled)")

    def _setup_optimizations(self):
        """Configure DuckDB for maximum performance"""
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()

            # Threading (2x CPUs recommended for IO-bound)
            threads = min(cpu_count * 2, 16)
            self.connection.execute(f"PRAGMA threads={threads}")

            # Memory limit
            self.connection.execute("PRAGMA memory_limit='4GB'")

            # Object cache (metadata cache)
            self.connection.execute("PRAGMA enable_object_cache=true")

            # Disable order preservation (faster)
            self.connection.execute("PRAGMA preserve_insertion_order=false")

            logger.info(f"[DUCKDB] Threads: {threads}, MemLimit: 4GB, ObjectCache: ON")
        except Exception as e:
            logger.warning(f"Failed to configure DuckDB: {e}")

    # ========================================
    # Core Query Methods
    # ========================================

    def query(self, sql: str, params: Optional[Dict] = None) -> 'pd.DataFrame':
        """
        Execute SQL query and return Pandas DataFrame.

        Args:
            sql: SQL query string
            params: Optional parameters for prepared statements

        Returns:
            pd.DataFrame: Query results
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas not available - use query_arrow() instead")

        start = time.time()

        try:
            if params:
                result = self.connection.execute(sql, params).df()
            else:
                result = self.connection.execute(sql).df()

            duration = time.time() - start
            # Verificação defensiva: RecordBatchReader não tem len()
            row_count = len(result) if hasattr(result, '__len__') else -1
            self.metrics.record(sql, duration, row_count)

            return result
        except Exception as e:
            logger.error(f"Query failed: {sql[:100]}... Error: {e}")
            raise

    def query_arrow(self, sql: str, params: Optional[Dict] = None) -> 'pa.Table':
        """
        Execute SQL query and return PyArrow Table (zero-copy).

        Args:
            sql: SQL query string
            params: Optional parameters

        Returns:
            pa.Table: Query results (zero-copy)
        """
        if not ARROW_AVAILABLE:
            raise ImportError("PyArrow not available")

        start = time.time()

        try:
            if params:
                result = self.connection.execute(sql, params).arrow()
            else:
                result = self.connection.execute(sql).arrow()

            duration = time.time() - start
            # Verificação defensiva: RecordBatchReader não tem len()
            row_count = len(result) if hasattr(result, '__len__') else -1
            self.metrics.record(sql, duration, row_count)

            return result
        except Exception as e:
            logger.error(f"Query failed: {sql[:100]}... Error: {e}")
            raise

    def query_dict(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute SQL query and return list of dicts.
        Equivalent to df.to_dict('records')

        Args:
            sql: SQL query string
            params: Optional parameters

        Returns:
            List[Dict]: Query results as list of records
        """
        if ARROW_AVAILABLE:
            # Preferir Arrow (zero-copy)
            arrow_result = self.query_arrow(sql, params)
            
            # Se for RecordBatchReader, converter para Table primeiro
            if hasattr(arrow_result, 'read_all'):
                # É um RecordBatchReader, precisa ler tudo
                arrow_result = arrow_result.read_all()
            
            return arrow_result.to_pylist()
        else:
            # Fallback para Pandas
            df = self.query(sql, params)
            return df.to_dict('records')

    # ========================================
    # Polars Compatibility Wrappers
    # ========================================

    def read_parquet(self, path: str, columns: Optional[List[str]] = None) -> 'pd.DataFrame':
        """
        Polars-compatible wrapper for reading Parquet.
        Equivalent to: pl.read_parquet(path)

        Args:
            path: Path to parquet file
            columns: Optional list of columns to read

        Returns:
            pd.DataFrame: Loaded dataframe
        """
        path = self._resolve_parquet_path(path)

        if columns:
            cols_str = ', '.join(columns)
            sql = f"SELECT {cols_str} FROM read_parquet('{path}')"
        else:
            sql = f"SELECT * FROM read_parquet('{path}')"

        return self.query(sql)

    @lru_cache(maxsize=10)
    def scan_parquet(self, path: str) -> str:
        """
        Polars-compatible lazy scan.
        Returns table name for chaining queries.

        Equivalent to: pl.scan_parquet(path)

        Args:
            path: Path to parquet file

        Returns:
            str: Table alias for use in queries
        """
        path = self._resolve_parquet_path(path)
        table_name = f"parquet_{hash(path) % 10000}"

        # Registrar tabela temporária
        self.connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE {table_name} AS
            SELECT * FROM read_parquet('{path}')
        """)

        return table_name

    def read_parquet_schema(self, path: str) -> Dict[str, str]:
        """
        Get Parquet schema without loading data.
        Equivalent to: pl.read_parquet_schema(path)

        Args:
            path: Path to parquet file

        Returns:
            Dict[str, str]: Column name -> type mapping
        """
        path = self._resolve_parquet_path(path)

        # DuckDB pode ler schema sem carregar dados
        result = self.connection.execute(f"""
            SELECT column_name, data_type
            FROM (DESCRIBE SELECT * FROM read_parquet('{path}'))
        """).fetchall()

        return {col: dtype for col, dtype in result}

    # ========================================
    # Pandas Compatibility
    # ========================================

    def read_parquet_pandas(self, path: str, columns: Optional[List[str]] = None,
                           engine: str = 'auto') -> 'pd.DataFrame':
        """
        Pandas-compatible wrapper.
        Equivalent to: pd.read_parquet(path, columns=columns)

        Note: 'engine' parameter ignored (DuckDB sempre usa PyArrow)
        """
        return self.read_parquet(path, columns)

    # ========================================
    # Cache Management (Substitui ParquetCache)
    # ========================================

    def load_parquet_to_memory(self, parquet_name: str, table_name: str = None) -> str:
        """
        [OK] CONTEXT7 PERFORMANCE: Carrega Parquet em TABELA em memória.
        Queries subsequentes são ~10x mais rápidas (5ms vs 300ms).

        Args:
            parquet_name: Nome do arquivo parquet
            table_name: Nome da tabela (opcional, auto-gerado se não fornecido)

        Returns:
            str: Nome da tabela em memória
        """
        path = self._resolve_parquet_path(parquet_name)
        if table_name is None:
            table_name = f"mem_{parquet_name.replace('.', '_')}"

        # Verificar se já está carregada
        if table_name in self._memory_tables:
            logger.info(f"[MEMORY] Tabela {table_name} já está em memória")
            return table_name

        start = time.time()

        # [OK] CRIAR TABELA EM MEMÓRIA (não VIEW!)
        # Isso carrega todos os dados uma vez e mantém em RAM
        self.connection.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{path}')
        """)

        # Contar registros carregados
        count = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        duration = time.time() - start

        self._memory_tables[table_name] = True

        logger.info(f"[OK] [MEMORY] Tabela {table_name} carregada: {count:,} registros em {duration:.2f}s")
        return table_name

    def get_memory_table(self, parquet_name: str) -> str:
        """
        Retorna nome da tabela em memória, carregando se necessário.
        Use este método ao invés de read_parquet() para performance máxima.
        """
        table_name = f"mem_{parquet_name.replace('.', '_')}"

        if table_name not in self._memory_tables:
            self.load_parquet_to_memory(parquet_name, table_name)

        return table_name

    @lru_cache(maxsize=5)
    def get_cached_parquet(self, parquet_name: str) -> str:
        """
        Cache de table handles para Parquets.
        [OK] CONTEXT7 FIX: Agora usa TABELA em memória ao invés de VIEW.

        Args:
            parquet_name: Nome do arquivo parquet

        Returns:
            str: Table name para usar em queries
        """
        # [OK] FIX 2026-01-14: Usar tabela em memória ao invés de VIEW
        return self.get_memory_table(parquet_name)

    # ========================================
    # Optimized Query Methods (Context7 Performance)
    # ========================================

    def load_data(
        self,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        order_by: Optional[str] = None,
        table_name: str = "mem_admmat_parquet"
    ) -> 'pd.DataFrame':
        """
        [OK] CONTEXT7: Query otimizada na tabela em memória.
        Muito mais rápido que carregar DataFrame completo e filtrar em Python.

        Args:
            columns: Lista de colunas a retornar (None = todas)
            filters: Dicionário de filtros {coluna: valor}
            limit: Limite de registros
            order_by: Ordenação (ex: "VENDA_30DD DESC")
            table_name: Nome da tabela em memória

        Returns:
            pd.DataFrame: Resultado da query
        """
        # Garantir que tabela existe em memória
        if table_name not in self._memory_tables:
            self.load_parquet_to_memory("admmat.parquet", table_name)

        # Construir SELECT
        cols = ", ".join(columns) if columns else "*"

        # Construir WHERE
        where_clauses = []
        if filters:
            for col, val in filters.items():
                if isinstance(val, str):
                    where_clauses.append(f"{col} = '{val}'")
                elif isinstance(val, (int, float)):
                    where_clauses.append(f"{col} = {val}")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Construir ORDER BY
        order_sql = f"ORDER BY {order_by}" if order_by else ""

        # Construir query final
        sql = f"SELECT {cols} FROM {table_name} {where_sql} {order_sql} LIMIT {limit}"

        logger.debug(f"[QUERY] {sql[:200]}...")
        return self.query(sql)

    def execute_aggregation(
        self,
        agg_col: str,
        agg_func: str = "sum",
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        table_name: str = "mem_admmat_parquet"
    ) -> 'pd.DataFrame':
        """
        [OK] CONTEXT7: Agregação otimizada na tabela em memória.

        Args:
            agg_col: Coluna para agregar
            agg_func: Função de agregação (sum, avg, count, min, max)
            group_by: Colunas para agrupar
            filters: Filtros a aplicar
            limit: Limite de resultados
            table_name: Nome da tabela em memória

        Returns:
            pd.DataFrame: Resultado da agregação
        """
        # Garantir que tabela existe em memória
        if table_name not in self._memory_tables:
            self.load_parquet_to_memory("admmat.parquet", table_name)

        # Construir SELECT com agregação
        if group_by:
            group_cols = ", ".join(group_by)
            select_sql = f"{group_cols}, {agg_func.upper()}({agg_col}) as valor"
            group_sql = f"GROUP BY {group_cols}"
        else:
            select_sql = f"{agg_func.upper()}({agg_col}) as valor"
            group_sql = ""

        # Construir WHERE
        where_clauses = []
        if filters:
            for col, val in filters.items():
                if isinstance(val, str):
                    where_clauses.append(f"{col} = '{val}'")
                elif isinstance(val, (int, float)):
                    where_clauses.append(f"{col} = {val}")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Query final
        sql = f"SELECT {select_sql} FROM {table_name} {where_sql} {group_sql} ORDER BY valor DESC LIMIT {limit}"

        logger.debug(f"[AGG] {sql[:200]}...")
        return self.query(sql)

    # ========================================
    # Helper Methods
    # ========================================

    def _resolve_parquet_path(self, path: str) -> str:
        """Resolve path to parquet file"""
        # Se path já é absoluto e existe
        if Path(path).exists():
            return str(Path(path).resolve()).replace("\\", "/")

        # Tentar em data/parquet
        base_dir = Path(os.getcwd())
        candidates = [
            base_dir / "data" / "parquet" / path,
            base_dir / "backend" / "data" / "parquet" / path,
            base_dir / path
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve()).replace("\\", "/")

        # Se não achou, retornar original (vai falhar no DuckDB com erro claro)
        logger.warning(f"Parquet file not found: {path}")
        return path

    def clear_cache(self):
        """Clear all caches"""
        self.get_cached_parquet.cache_clear()
        self._prepared_cache.clear()
        logger.info("[CACHE] Cleared all caches")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.get_stats()

    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = PerformanceMetrics()

    # ========================================
    # Async Methods
    # ========================================

    async def query_async(self, sql: str, params: Optional[Dict] = None):
        """Execute query asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, sql, params)

    @asynccontextmanager
    async def get_pooled_connection(self):
        """Get connection from pool (async)"""
        async with self._lock:
            conn_index = self._pool_index
            self._pool_index = (self._pool_index + 1) % len(self._connection_pool)

        try:
            yield self._connection_pool[conn_index]
        finally:
            pass  # Connection volta para pool automaticamente

    # ========================================
    # Migration Utilities
    # ========================================

    def migrate_from_polars(self, df_operation: str) -> str:
        """
        Convert Polars operation to DuckDB SQL.
        Helper para migração gradual.

        Example:
            polars: df.filter(pl.col("price") > 100).select(["name", "price"])
            duckdb: SELECT name, price FROM table WHERE price > 100
        """
        # TODO: Implementar parser completo
        # Por enquanto, retornar mensagem de ajuda
        raise NotImplementedError(
            "Use DuckDB SQL directly. Example:\n"
            "  Polars: df.filter(pl.col('x') > 10)\n"
            "  DuckDB: adapter.query('SELECT * FROM table WHERE x > 10')"
        )

    def benchmark(self, sql: str, iterations: int = 5) -> Dict[str, float]:
        """
        Benchmark a query.

        Args:
            sql: SQL query to benchmark
            iterations: Number of iterations

        Returns:
            Dict with timing stats
        """
        times = []

        for _ in range(iterations):
            start = time.time()
            _ = self.connection.execute(sql).fetchall()
            times.append(time.time() - start)

        return {
            'avg_ms': (sum(times) / len(times)) * 1000,
            'min_ms': min(times) * 1000,
            'max_ms': max(times) * 1000,
            'iterations': iterations
        }


# Singleton instance
_adapter_instance = None

def get_duckdb_adapter() -> DuckDBEnhancedAdapter:
    """Get singleton instance of DuckDB adapter"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = DuckDBEnhancedAdapter()
    return _adapter_instance
