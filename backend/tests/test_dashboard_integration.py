import sys
import os
import pytest
from fastapi.testclient import TestClient

# Adicionar root ao path para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from main import app
except ImportError:
    # Fallback structure
    from app.main import app

client = TestClient(app)

def test_suppliers_metrics():
    """Testa se o endpoint de fornecedores retorna dados e status 200"""
    print("\nTesting /dashboard/suppliers/metrics...")
    response = client.get("/api/v1/dashboard/suppliers/metrics")
    
    # Debug response
    if response.status_code != 200:
        print(f"Error: {response.text}")
        
    assert response.status_code == 200
    data = response.json()
    assert "suppliers" in data
    assert isinstance(data["suppliers"], list)
    
    if len(data["suppliers"]) > 0:
        s = data["suppliers"][0]
        assert "nome" in s
        assert "taxa_ruptura" in s
        print(f"Sample Supplier: {s['nome']} | Ruptura: {s['taxa_ruptura']}")
    else:
        print("Warning: No suppliers returned (but endpoint worked)")

def test_forecast_tool():
    """Testa se o endpoint de previsão retorna dados e status 200"""
    print("\nTesting /dashboard/tools/prever_demanda_sazonal...")
    payload = {
        "produto_id": "59294",
        "periodo_dias": 30,
        "considerar_sazonalidade": True
    }
    response = client.post("/api/v1/dashboard/tools/prever_demanda_sazonal", json=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        
    assert response.status_code == 200
    data = response.json()
    
    if "error" in data:
        # Se retornar erro de negócio (ex: histórico insuficiente), ainda é 200 OK na API
        print(f"API Returned Business Error: {data['error']}")
        # Validar estrutura de erro
        assert "produto" in data
    else:
        # Sucesso
        assert "forecast" in data
        assert "forecast_ajustado" in data
        print(f"Forecast Generated: {len(data['forecast'])} periods")

def test_eoq_tool():
    """Testa se o endpoint de EOQ retorna dados e status 200"""
    print("\nTesting /dashboard/tools/calcular_eoq...")
    payload = {
        "produto_id": "59294"
    }
    response = client.post("/api/v1/dashboard/tools/calcular_eoq", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    if "error" in data:
        print(f"API Returned Business Error: {data['error']}")
    else:
        assert "eoq" in data
        print(f"EOQ: {data['eoq']}")

if __name__ == "__main__":
    # Executar manualmente se chamado direto
    try:
        test_suppliers_metrics()
        test_forecast_tool()
        test_eoq_tool()
        print("\n✅ ALL TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
