"""
SQLAgent — Agente de Consultas SQL

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import Any, Dict, List, Optional
import structlog
import duckdb

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse

logger = structlog.get_logger(__name__)


class SQLAgent(BaseAgent):
    """Agente responsável por consultas SQL."""
    
    def __init__(self, db_path: str = "data/analytics.duckdb"):
        super().__init__(
            name="SQLAgent",
            description="Executa consultas SQL analíticas",
            capabilities=["query", "aggregate", "filter"]
        )
        self.db_path = db_path
        self._conn = None
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
        return self._conn
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        # Extrai SQL do request (simplificado)
        result = await self.query(request.content)
        return AgentResponse(
            content=str(result[:5]) if result else "Sem resultados",
            agent_name=self.name,
            metadata={"row_count": len(result) if result else 0}
        )
    
    async def query(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executa query SQL e retorna resultados."""
        try:
            conn = self._get_connection()
            if params:
                result = conn.execute(sql, params).fetchall()
            else:
                result = conn.execute(sql).fetchall()
            
            # Converte para lista de dicts
            columns = [desc[0] for desc in conn.description] if conn.description else []
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            logger.error("sql_query_failed", error=str(e), sql=sql[:100])
            return []
    
    async def query_parquet(self, parquet_path: str, sql_template: str) -> List[Dict[str, Any]]:
        """Query em arquivo Parquet."""
        sql = sql_template.replace("{table}", f"read_parquet('{parquet_path}')")
        return await self.query(sql)
    
    async def get_schema(self, table_or_path: str) -> List[Dict[str, str]]:
        """Retorna schema de tabela ou arquivo."""
        if table_or_path.endswith('.parquet'):
            sql = f"DESCRIBE SELECT * FROM read_parquet('{table_or_path}') LIMIT 1"
        else:
            sql = f"DESCRIBE {table_or_path}"
        return await self.query(sql)
    
    async def aggregate(
        self, table: str, group_by: List[str], metrics: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Executa agregação."""
        metrics_sql = ", ".join(f"{func}({col}) as {col}_{func}" for col, func in metrics.items())
        group_sql = ", ".join(group_by)
        sql = f"SELECT {group_sql}, {metrics_sql} FROM {table} GROUP BY {group_sql}"
        return await self.query(sql)
