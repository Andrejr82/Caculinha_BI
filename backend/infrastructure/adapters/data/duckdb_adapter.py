"""
DuckDBAdapter - Adapter para DuckDB/Parquet

Implementa DataSourcePort para acesso real aos arquivos Parquet.

Uso:
    from backend.infrastructure.adapters.data import DuckDBAdapter
    
    adapter = DuckDBAdapter(parquet_dir="./data/parquet")
    result = await adapter.execute_query("SELECT * FROM admmat LIMIT 10")

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import duckdb
import structlog

from backend.domain.ports.data_source_port import (
    DataSourcePort,
    QueryResult,
    ColumnInfo,
)


logger = structlog.get_logger(__name__)


class DuckDBAdapter(DataSourcePort):
    """
    Adapter real para DuckDB com suporte a Parquet.
    
    Implementa DataSourcePort usando DuckDB para queries SQL
    diretamente nos arquivos Parquet do projeto.
    
    Example:
        >>> adapter = DuckDBAdapter(parquet_dir="./data/parquet")
        >>> result = await adapter.execute_query(
        ...     "SELECT COD_PRODUTO, SUM(QUANTIDADE) FROM admmat GROUP BY 1"
        ... )
        >>> print(result.row_count)
    """
    
    def __init__(
        self,
        parquet_dir: Optional[str] = None,
        database_path: str = ":memory:",
    ):
        """
        Inicializa o DuckDBAdapter.
        
        Args:
            parquet_dir: Diretório contendo arquivos Parquet
            database_path: Caminho do banco DuckDB (default: in-memory)
        """
        self._parquet_dir = parquet_dir or os.getenv(
            "PARQUET_DIR",
            str(Path(__file__).parent.parent.parent.parent.parent / "data" / "parquet")
        )
        self._database_path = database_path
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._registered_tables: List[str] = []
        
        logger.info(
            "duckdb_adapter_initialized",
            parquet_dir=self._parquet_dir,
            database_path=self._database_path,
        )
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Obtém ou cria conexão com DuckDB."""
        if self._connection is None:
            self._connection = duckdb.connect(self._database_path)
            self._register_parquet_files()
        return self._connection
    
    def _register_parquet_files(self) -> None:
        """Registra arquivos Parquet como views no DuckDB."""
        parquet_path = Path(self._parquet_dir)
        
        if not parquet_path.exists():
            logger.warning("parquet_dir_not_found", path=self._parquet_dir)
            return
        
        for file in parquet_path.glob("*.parquet"):
            table_name = file.stem  # Nome sem extensão
            try:
                self._connection.execute(f"""
                    CREATE OR REPLACE VIEW {table_name} AS 
                    SELECT * FROM read_parquet('{file.as_posix()}')
                """)
                self._registered_tables.append(table_name)
                logger.info("parquet_registered", table=table_name, path=str(file))
            except Exception as e:
                logger.error("parquet_register_error", table=table_name, error=str(e))
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Executa uma query SQL.
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para substituição
        
        Returns:
            QueryResult com os dados
        """
        conn = self._get_connection()
        start_time = time.time()
        
        try:
            # Executar query
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)
            
            # Obter resultados
            columns = [desc[0] for desc in result.description] if result.description else []
            rows = result.fetchall()
            
            # Converter para lista de dicionários
            data = [dict(zip(columns, row)) for row in rows]
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                "query_executed",
                row_count=len(data),
                execution_time_ms=execution_time,
                query_preview=query[:100],
            )
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=len(data),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error("query_execution_error", error=str(e), query=query[:200])
            raise
    
    async def get_columns(self, table: str) -> List[ColumnInfo]:
        """
        Retorna informações sobre as colunas de uma tabela.
        
        Args:
            table: Nome da tabela
        
        Returns:
            Lista de ColumnInfo
        """
        conn = self._get_connection()
        
        try:
            result = conn.execute(f"DESCRIBE {table}")
            rows = result.fetchall()
            
            columns = []
            for row in rows:
                columns.append(ColumnInfo(
                    name=row[0],
                    dtype=row[1],
                    nullable=row[2] == "YES" if len(row) > 2 else True,
                    description=None,
                ))
            
            return columns
            
        except Exception as e:
            logger.error("get_columns_error", table=table, error=str(e))
            return []
    
    async def get_tables(self) -> List[str]:
        """
        Retorna a lista de tabelas disponíveis.
        
        Returns:
            Lista de nomes de tabelas
        """
        if not self._registered_tables:
            self._get_connection()  # Força registro de parquets
        
        return self._registered_tables.copy()
    
    async def table_exists(self, table: str) -> bool:
        """
        Verifica se uma tabela existe.
        
        Args:
            table: Nome da tabela
        
        Returns:
            True se existir
        """
        tables = await self.get_tables()
        return table.lower() in [t.lower() for t in tables]
    
    async def get_row_count(self, table: str) -> int:
        """
        Retorna o número de linhas em uma tabela.
        
        Args:
            table: Nome da tabela
        
        Returns:
            Número de linhas
        """
        result = await self.execute_query(f"SELECT COUNT(*) as cnt FROM {table}")
        if result.data:
            return result.data[0].get("cnt", 0)
        return 0
    
    async def health_check(self) -> bool:
        """
        Verifica se a conexão está saudável.
        
        Returns:
            True se saudável
        """
        try:
            conn = self._get_connection()
            result = conn.execute("SELECT 1")
            return result.fetchone() is not None
        except Exception:
            return False
    
    def close(self) -> None:
        """Fecha a conexão com o banco."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("duckdb_connection_closed")
