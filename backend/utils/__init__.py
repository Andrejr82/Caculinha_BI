"""
Utils Package - Módulos utilitários para o BI Solution
FIX 2026-02-04: Novo pacote com validação SQL e execução segura de queries
"""

from .sql_validator import (
    SQLValidator,
    SQLValidationError,
    validate_sql,
    safe_add_limit,
    sanitize_query
)

from .query_executor import (
    QueryExecutor,
    QueryTimeoutError,
    get_executor,
    execute_query,
    execute_query_safe
)

__all__ = [
    # SQL Validator
    "SQLValidator",
    "SQLValidationError",
    "validate_sql",
    "safe_add_limit",
    "sanitize_query",
    
    # Query Executor
    "QueryExecutor",
    "QueryTimeoutError",
    "get_executor",
    "execute_query",
    "execute_query_safe"
]
