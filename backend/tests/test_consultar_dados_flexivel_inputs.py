
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel

# Mock do cache e adapter
@pytest.fixture
def mock_cache():
    with patch("app.core.parquet_cache.cache") as mock:
        mock._adapter.get_memory_table.return_value = "admmat.parquet"
        mock._adapter.query.return_value = pd.DataFrame([
            {"CODIGO": 123, "NOME": "PRODUTO TESTE", "NOMESEGMENTO": "TESTE"}
        ])
        yield mock

def test_inputs_dict_list_int(mock_cache):
    """Teste inputs nativos (dict, list, int)."""
    
    # Input estruturado - Usando .invoke com dicionário
    result = consultar_dados_flexivel.invoke({
        "filtros": {"NOMESEGMENTO": "TESTE"},
        "colunas": ["CODIGO", "NOME"],
        "limite": 50,
        "agrupar_por": ["NOMESEGMENTO"]
    })
    
    assert result["total_resultados"] == 1

def test_inputs_str_json(mock_cache):
    """Teste inputs string JSON (compatibilidade)."""
    
    # Input JSON string
    result = consultar_dados_flexivel.invoke({
        "filtros": '{"NOMESEGMENTO": "TESTE"}',
        "colunas": '["CODIGO", "NOME"]',
        "limite": "50",
        "agrupar_por": '["NOMESEGMENTO"]'
    })
    
    assert result["total_resultados"] == 1

def test_inputs_str_csv(mock_cache):
    """Teste inputs string CSV (compatibilidade simples)."""
    
    result = consultar_dados_flexivel.invoke({
        "colunas": "CODIGO, NOME",
        "limite": "10",
        "agrupar_por": "NOMESEGMENTO"
    })
    
    assert result["total_resultados"] == 1

def test_inputs_mixed(mock_cache):
    """Teste inputs mistos."""
    
    result = consultar_dados_flexivel.invoke({
        "filtros": {"NOMESEGMENTO": "TESTE"},  # Dict
        "colunas": '["CODIGO", "NOME"]',      # JSON Str
        "limite": 10                           # Int
    })
    
    assert result["total_resultados"] == 1

def test_inputs_invalid_json(mock_cache):
    """Teste inputs JSON inválido (deve degradar graciosamente)."""
    
    # JSON quebrado em filtros
    result = consultar_dados_flexivel.invoke({
        "filtros": '{"NOMESEGMENTO": "TESTE"', # Faltando chave
        "limite": 10
    })
    
    # Não deve crashar, apenas ignorar filtro ou logar warning
    assert "error" not in result
