
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import duckdb

# Importando a implementação concreta
from backend.app.infrastructure.data.duckdb_enhanced_adapter import DuckDBEnhancedAdapter, get_duckdb_adapter

@pytest.fixture
def adapter():
    """
    Retorna uma instância limpa do adapter para cada teste.
    Reseta o singleton para garantir isolamento.
    """
    # Reset singleton
    import backend.app.infrastructure.data.duckdb_enhanced_adapter as mod
    
    # Reset variavel global do modulo
    mod._adapter_instance = None
    # Reset variavel de classe (Singleton via __new__)
    DuckDBEnhancedAdapter._instance = None
    
    # Instancia novo adapter
    adapter = get_duckdb_adapter()
    
    yield adapter
    
    # Teardown
    try:
        adapter.connection.close()
    except:
        pass
    mod._adapter_instance = None
    DuckDBEnhancedAdapter._instance = None


def test_singleton_pattern():
    """Valida se get_duckdb_adapter retorna a mesma instância."""
    a1 = get_duckdb_adapter()
    a2 = get_duckdb_adapter()
    assert a1 is a2

def test_query_returns_dataframe(adapter):
    """Contrato: query(sql) deve retornar pandas DataFrame."""
    # Setup
    adapter.connection.execute("CREATE OR REPLACE TABLE test_table (id INTEGER, name VARCHAR)")
    adapter.connection.execute("INSERT INTO test_table VALUES (1, 'Test')")
    
    # Act
    df = adapter.query("SELECT * FROM test_table")
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['id'] == 1
    assert df.iloc[0]['name'] == 'Test'

def test_query_dict_returns_list_of_dicts(adapter):
    """Contrato: query_dict(sql) deve retornar List[Dict]."""
    # Setup
    adapter.connection.execute("CREATE OR REPLACE TABLE test_table (id INTEGER, name VARCHAR)")
    adapter.connection.execute("INSERT INTO test_table VALUES (1, 'Test'), (2, 'Test2')")
    
    # Act
    result = adapter.query_dict("SELECT * FROM test_table ORDER BY id")
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], dict)
    assert result[0]['name'] == 'Test'
    assert result[1]['name'] == 'Test2'

def test_load_parquet_to_memory(adapter, tmp_path):
    """Contrato: load_parquet_to_memory deve carregar arquivo e retornar nome da tabela."""
    # Setup: Criar parquet fake
    df = pd.DataFrame({'col1': [1, 2, 3]})
    parquet_path = tmp_path / "test.parquet"
    df.to_parquet(parquet_path)
    
    # Act
    # Mock _resolve_parquet_path para usar nosso tmp_path
    with patch.object(adapter, '_resolve_parquet_path', return_value=str(parquet_path)) as mock_resolve:
        table_name = adapter.load_parquet_to_memory("test.parquet")
    
    # Assert
    assert table_name.startswith("mem_test")
    
    # Verificar se tabela existe realmente na memória
    result = adapter.query(f"SELECT * FROM {table_name}")
    assert len(result) == 3
    assert result.iloc[0]['col1'] == 1

def test_invalid_sql_raises_exception(adapter):
    """Contrato: SQL inválido deve levantar exceção (não silenciar)."""
    with pytest.raises(Exception): # Pode ser duckdb.Error ou Exception genérica
        adapter.query("SELECT * FROM tabela_inexistente")
