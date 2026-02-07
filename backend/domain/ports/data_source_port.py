"""
Port: DataSourcePort

Interface abstrata para acesso a fontes de dados.
Implementada por: DuckDBAdapter, ParquetRepository

Uso:
    from backend.domain.ports import DataSourcePort
    
    class DuckDBAdapter(DataSourcePort):
        async def execute_query(self, query, params=None):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """
    Resultado de uma query executada.
    
    Attributes:
        data: Lista de registros (dicionários)
        columns: Nomes das colunas
        row_count: Número de linhas retornadas
        execution_time_ms: Tempo de execução em milissegundos
    """
    
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float


@dataclass
class ColumnInfo:
    """
    Informações sobre uma coluna.
    
    Attributes:
        name: Nome da coluna
        dtype: Tipo de dado
        nullable: Se aceita nulos
        description: Descrição opcional
    """
    
    name: str
    dtype: str
    nullable: bool = True
    description: Optional[str] = None


class DataSourcePort(ABC):
    """
    Interface abstrata para acesso a fontes de dados.
    
    Esta é a porta principal para consultas a dados analíticos.
    Implementações concretas em infrastructure/adapters/data/
    
    Example:
        >>> class DuckDBAdapter(DataSourcePort):
        ...     async def execute_query(self, query, params=None):
        ...         # Implementação específica do DuckDB
        ...         pass
    """
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Executa uma query SQL e retorna os resultados.
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para substituição na query
        
        Returns:
            QueryResult com os dados
        
        Raises:
            DataSourceError: Em caso de erro na execução
        """
        pass
    
    @abstractmethod
    async def get_columns(self, table: str) -> List[ColumnInfo]:
        """
        Retorna informações sobre as colunas de uma tabela.
        
        Args:
            table: Nome da tabela
        
        Returns:
            Lista de ColumnInfo
        """
        pass
    
    @abstractmethod
    async def get_tables(self) -> List[str]:
        """
        Retorna a lista de tabelas disponíveis.
        
        Returns:
            Lista de nomes de tabelas
        """
        pass
    
    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        """
        Verifica se uma tabela existe.
        
        Args:
            table: Nome da tabela
        
        Returns:
            True se existir, False caso contrário
        """
        pass
    
    @abstractmethod
    async def get_row_count(self, table: str) -> int:
        """
        Retorna o número de linhas em uma tabela.
        
        Args:
            table: Nome da tabela
        
        Returns:
            Número de linhas
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica se a conexão com a fonte de dados está saudável.
        
        Returns:
            True se saudável, False caso contrário
        """
        pass
