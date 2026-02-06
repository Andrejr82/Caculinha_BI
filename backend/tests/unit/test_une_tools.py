# backend/tests/unit/test_une_tools.py

import pytest
from app.core.tools.une_tools import (
    calcular_abastecimento_une,
    calcular_mc_produto,
    calcular_preco_final_une,
    validar_transferencia_produto,
    sugerir_transferencias_automaticas,
    encontrar_rupturas_criticas,
    _get_data_adapter,
    _normalize_dataframe,
    _load_data
)
from app.infrastructure.data.hybrid_adapter import HybridDataAdapter

# Mocking the HybridDataAdapter to control test data
@pytest.fixture
def mock_hybrid_adapter():
    class MockHybridAdapter(HybridDataAdapter):
        def fetch_data(self, filters: dict, columns: list = None) -> list:
            # Simulate some data for testing
            all_data = [
                {"une_id": 1, "produto_id": 101, "segmento": "A", "media_considerada_lv": 10.0, "estoque_origem": 50, "estoque_destino": 20, "linha_verde": 30, "vendas_diarias": 5.0, "transferencias_pendentes": 0, "criticidade": "NORMAL"},
                {"une_id": 1, "produto_id": 102, "segmento": "A", "media_considerada_lv": 20.0, "estoque_origem": 10, "estoque_destino": 5, "linha_verde": 40, "vendas_diarias": 10.0, "transferencias_pendentes": 0, "criticidade": "URGENTE"},
                {"une_id": 2, "produto_id": 101, "segmento": "B", "media_considerada_lv": 15.0, "estoque_origem": 100, "estoque_destino": 80, "linha_verde": 20, "vendas_diarias": 7.0, "transferencias_pendentes": 0, "criticidade": "NORMAL"},
                {"une_id": 3, "produto_id": 103, "segmento": "C", "media_considerada_lv": 5.0, "estoque_origem": 5, "estoque_destino": 2, "linha_verde": 10, "vendas_diarias": 1.0, "transferencias_pendentes": 0, "criticidade": "ALTA"},
                {"une_id": 4, "produto_id": 102, "segmento": "A", "media_considerada_lv": 25.0, "estoque_origem": 60, "estoque_destino": 10, "linha_verde": 20, "vendas_diarias": 12.0, "transferencias_pendentes": 0, "criticidade": "NORMAL"},
                {"une_id": 1, "produto_id": 103, "segmento": "C", "media_considerada_lv": 5.0, "estoque_origem": 2, "estoque_destino": 2, "linha_verde": 10, "vendas_diarias": 1.0, "transferencias_pendentes": 0, "criticidade": "URGENTE"}, # Rupture test
            ]

            filtered_data = []
            for item in all_data:
                match = True
                for key, value in filters.items():
                    if isinstance(value, dict) and '$ne' in value: # Handle "$ne" for not equals
                        if key in item and item[key] == value['$ne']:
                            match = False
                            break
                    elif key in item and item[key] != value:
                        match = False
                        break
                if match:
                    filtered_data.append(item)
            
            if columns:
                return [{col: item.get(col) for col in columns} for item in filtered_data]
            return filtered_data
    
    # Patch the _get_data_adapter to return our mock
    # This is a simplification; in a real app, you might use dependency injection
    # or a more robust mocking framework like unittest.mock.patch
    _get_data_adapter.cache_clear() # Clear lru_cache before patching
    original_adapter = _get_data_adapter.__wrapped__ # Get the original function
    _get_data_adapter.__wrapped__ = lambda: MockHybridAdapter()
    yield
    _get_data_adapter.__wrapped__ = original_adapter # Restore original adapter after test

# Test _normalize_dataframe
def test_normalize_dataframe():
    data = [{"UNE_ID": 1, "Produto_ID": 101}]
    normalized = _normalize_dataframe(data)
    assert normalized == [{"une_id": 1, "produto_id": 101}]

# Test _load_data
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_load_data_basic_filter():
    data = _load_data(filters={"une_id": 1})
    assert len(data) == 3
    assert all(item['une_id'] == 1 for item in data)

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_load_data_with_columns():
    data = _load_data(filters={"une_id": 1}, columns=["produto_id"])
    assert len(data) == 3
    assert all('une_id' not in item for item in data)
    assert all('produto_id' in item for item in data)

# Test calcular_abastecimento_une
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_abastecimento_une_urgente():
    result = calcular_abastecimento_une(une_id=1, limite=10)
    assert any(item.get("produto_id") == 102 and item.get("criticidade_abastecimento") == "URGENTE" for item in result)
    assert len(result) == 3 # All items for une_id 1

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_abastecimento_une_normal():
    result = calcular_abastecimento_une(une_id=2)
    assert len(result) == 1
    assert result[0]["criticidade_abastecimento"] == "NORMAL"

# Test calcular_mc_produto
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_mc_produto_found():
    result = calcular_mc_produto(produto_id=101, une_id=1)
    assert result["produto_id"] == 101
    assert result["une_id"] == 1
    assert "mc_calculada" in result
    assert result["mc_calculada"] == 2.5 # 10.0 * 0.25

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_mc_produto_not_found():
    result = calcular_mc_produto(produto_id=999, une_id=1)
    assert result["mc_calculada"] is None
    assert "Dados não encontrados" in result["mensagem"]

# Test calcular_preco_final_une
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_preco_final_une_found():
    result = calcular_preco_final_une(produto_id=101, une_id=1)
    assert result["produto_id"] == 101
    assert result["une_id"] == 1
    assert "preco_final" in result
    assert result["preco_final"] == pytest.approx(10.0 * 1.10 * 1.05) # ~11.55

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_calcular_preco_final_une_not_found():
    result = calcular_preco_final_une(produto_id=999, une_id=1)
    assert result["preco_final"] is None
    assert "Não foi possível calcular o preço final" in result["mensagem"]

# Test validar_transferencia_produto
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_validar_transferencia_produto_sucesso():
    result = validar_transferencia_produto(produto_id=101, une_origem=2, une_destino=1, quantidade=10)
    assert result["status"] == "sucesso"

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_validar_transferencia_produto_estoque_insuficiente():
    result = validar_transferencia_produto(produto_id=101, une_origem=1, une_destino=2, quantidade=100)
    assert result["status"] == "falha"
    assert "Estoque insuficiente" in result["mensagem"]

@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_validar_transferencia_produto_excede_lv_alerta():
    # une_id 1, produto_id 101: estoque_origem=50, linha_verde=30
    # Current stock at destination (une 2, prod 101) is 100, LV=20.
    # If we transfer 10 from une 1 to une 2: new stock at dest = 100+10 = 110.
    # LV=20. 1.2 * LV = 24. 110 > 24, so it should trigger an alert.
    result = validar_transferencia_produto(produto_id=101, une_origem=1, une_destino=2, quantidade=10)
    assert result["status"] == "alerta"
    assert "exceder significativamente a Linha Verde" in result["mensagem"]

# Test encontrar_rupturas_criticas
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_encontrar_rupturas_criticas_urgente():
    result = encontrar_rupturas_criticas(limite=10)
    assert any(item.get("produto_id") == 103 and item.get("une_id") == 1 and item.get("criticidade_ruptura") == "URGENTE" for item in result)
    assert any(item.get("produto_id") == 102 and item.get("une_id") == 1 and item.get("criticidade_ruptura") == "URGENTE" for item in result)
    
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_encontrar_rupturas_criticas_alta():
    result = encontrar_rupturas_criticas(limite=10)
    assert any(item.get("produto_id") == 103 and item.get("une_id") == 3 and item.get("criticidade_ruptura") == "ALTA" for item in result)


# Test sugerir_transferencias_automaticas
@pytest.mark.usefixtures("mock_hybrid_adapter")
def test_sugerir_transferencias_automaticas_basic():
    # Mock some data to ensure rupture product 103 in UNE 1 is urgent (estoque 2, LV 10, vendas 1 -> days_cobertura 2)
    # Then find an origin for product 103 that has stock
    # UNE 3, produto 103 has estoque_origem=5, LV=10. This could be an origin if UNE 1 is the destination.

    suggestions = sugerir_transferencias_automaticas(limite=1)
    # The current mock data logic for _load_data and encontrar_rupturas_criticas
    # should prioritize (103,1) as URGENTE rupture.
    # Then search for (103, X) in other UNEs. UNE 3, produto 103, estoque 5.
    # Target (103,1) needs 8 (LV 10 - stock 2). Origin (103,3) has 5.
    
    assert len(suggestions) >= 1
    assert suggestions[0]["produto_id"] == 103
    assert suggestions[0]["une_destino"] == 1
    assert suggestions[0]["une_origem"] == 3 # Expected based on mock data and logic
    assert suggestions[0]["quantidade_sugerida"] == 8

