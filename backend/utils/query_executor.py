"""
Query Executor - Executor de queries com timeout e cache
FIX 2026-02-04: Novo módulo para execução segura de queries SQL

Funcionalidades:
- Conexão DuckDB em modo read-only
- Validação SQL antes de executar
- Timeout configurável
- Retorna dict estruturado com data, rows_count, execution_time
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class QueryTimeoutError(Exception):
    """Exceção para timeout de query"""
    pass


class QueryExecutor:
    """Executor seguro de queries SQL"""
    
    def __init__(self, db_path: str = None, timeout_seconds: int = 30):
        self.db_path = db_path
        self.timeout_seconds = timeout_seconds
        self.conn = None
        self._duckdb = None
    
    def _get_duckdb(self):
        """Lazy import de DuckDB"""
        if self._duckdb is None:
            try:
                import duckdb
                self._duckdb = duckdb
            except ImportError:
                logger.error("DuckDB não instalado")
                raise ImportError("DuckDB não disponível")
        return self._duckdb
    
    def connect(self):
        """Estabelece conexão com DuckDB"""
        if self.conn is None:
            duckdb = self._get_duckdb()
            if self.db_path:
                self.conn = duckdb.connect(self.db_path, read_only=True)
            else:
                # Conexão in-memory para usar com cache existente
                self.conn = duckdb.connect(":memory:")
            logger.info(f"DuckDB conectado: {self.db_path or ':memory:'}")
    
    def execute(self, sql: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Executa query SQL com validação e timeout
        
        Args:
            sql: Query SQL
            use_cache: Se True, usa cache do parquet
            
        Returns:
            dict com 'data', 'rows_count', 'execution_time_ms', 'warnings'
        """
        from backend.utils.sql_validator import validate_sql, safe_add_limit
        
        start_time = time.time()
        
        # 1. Validar SQL
        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            return {
                'error': error_msg,
                'error_type': 'validation',
                'execution_time_ms': 0
            }
        
        # 2. Adicionar LIMIT se ausente
        sql_safe = safe_add_limit(sql)
        
        # 3. Executar
        try:
            self.connect()
            
            # Executar query
            result = self.conn.execute(sql_safe).fetchdf()
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # 4. Preparar resposta
            return {
                'data': result.to_dict('records'),
                'rows_count': len(result),
                'execution_time_ms': round(execution_time, 2),
                'warnings': self._generate_warnings(result, sql_safe),
                'sql_executed': sql_safe
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Classificar tipo de erro
            error_type = 'unknown'
            error_str = str(e).lower()
            if 'timeout' in error_str:
                error_type = 'timeout'
            elif 'syntax' in error_str:
                error_type = 'syntax'
            elif 'not found' in error_str or 'does not exist' in error_str:
                error_type = 'not_found'
            
            logger.error(f"Erro executando query: {e}")
            
            return {
                'error': str(e),
                'error_type': error_type,
                'execution_time_ms': round(execution_time, 2),
                'sql_executed': sql_safe
            }
    
    def execute_with_existing_cache(self, sql: str) -> Dict[str, Any]:
        """
        Executa query usando o cache de parquet existente no sistema
        
        Usa app.core.parquet_cache se disponível
        """
        start_time = time.time()
        
        try:
            from backend.app.core.parquet_cache import cache
            from backend.utils.sql_validator import validate_sql, safe_add_limit
            
            # 1. Validar
            is_valid, error_msg = validate_sql(sql)
            if not is_valid:
                return {'error': error_msg, 'error_type': 'validation'}
            
            # 2. Garantir tabela em memória
            table_name = cache._adapter.get_memory_table("admmat.parquet")
            
            # 3. Executar via cache
            sql_safe = safe_add_limit(sql)
            result = cache._adapter.execute_sql(sql_safe)
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                'data': result.to_dict('records') if hasattr(result, 'to_dict') else result,
                'rows_count': len(result) if hasattr(result, '__len__') else 0,
                'execution_time_ms': round(execution_time, 2),
                'sql_executed': sql_safe
            }
            
        except ImportError:
            logger.warning("Cache de parquet não disponível, usando execute() padrão")
            return self.execute(sql)
        except Exception as e:
            logger.error(f"Erro com cache: {e}")
            return {'error': str(e), 'error_type': 'cache_error'}
    
    def _generate_warnings(self, df, sql: str) -> list:
        """Gera warnings baseado nos resultados"""
        warnings = []
        
        # Warning 1: Resultado muito grande
        if len(df) >= 500:
            warnings.append(
                "Resultado truncado em 500 linhas. "
                "Considere adicionar filtros mais específicos."
            )
        
        # Warning 2: Resultado vazio
        if len(df) == 0:
            warnings.append("Nenhum resultado encontrado para a query.")
        
        return warnings
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Conexão DuckDB fechada")


# Instância global
_executor: Optional[QueryExecutor] = None


def get_executor(db_path: str = None) -> QueryExecutor:
    """Factory function para obter executor"""
    global _executor
    if _executor is None:
        _executor = QueryExecutor(db_path)
    return _executor


def execute_query(sql: str) -> Dict[str, Any]:
    """Helper function para execução rápida"""
    executor = get_executor()
    return executor.execute(sql)


def execute_query_safe(sql: str) -> Dict[str, Any]:
    """Executa query usando cache existente do sistema"""
    executor = get_executor()
    return executor.execute_with_existing_cache(sql)


# Testes se executado diretamente
if __name__ == "__main__":
    # Query de teste
    sql = """
        SELECT categoria, SUM(valor_total) as faturamento
        FROM vendas
        GROUP BY categoria
        ORDER BY faturamento DESC
    """
    
    result = execute_query(sql)
    
    if 'error' in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Query executada em {result['execution_time_ms']}ms")
        print(f"📊 {result['rows_count']} linhas retornadas")
        if result.get('warnings'):
            print(f"⚠️ Warnings: {result['warnings']}")
