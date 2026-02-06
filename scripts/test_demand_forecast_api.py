
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1/dashboard"

def test_demand_forecast():
    print("Testing Demand Forecast API (Prever Demanda)...")
    url = f"{BASE_URL}/tools/prever_demanda"
    payload = {
        "produto_id": "59294",
        "periodo_dias": 30,
        "considerar_sazonalidade": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Check for 'abrangencia'
        if "abrangencia" in data:
            print(f"✅ 'abrangencia' field found.")
            print(f"   Total Payloads: {data['abrangencia']['total_lojas']}")
            # print(f"   Details: {data['abrangencia']['detalhes']}")
            
            # Teste com filtro de loja
            print("\nTesting Forecast API (Loja Específica)...")
            payload_loja = payload.copy()
            payload_loja["une"] = "1"
            
            response_loja = requests.post(url, json=payload_loja)
            response_loja.raise_for_status()
            data_loja = response_loja.json()
            
            if "abrangencia" in data_loja and data_loja['abrangencia']['filtro_aplicado'] == "1":
                 print(f"✅ Filtro de Loja 1 aplicado com sucesso.")
            else:
                 print(f"❌ Falha no filtro de loja.")
        else:
            print("❌ 'abrangencia' field NOT found in response.")
            return False

        return True
    except Exception as e:
        print(f"❌ Error testing forecast: {e}")
        return False

def test_allocation():
    print("\nTesting Allocation API (Alocar Estoque)...")
    url = f"{BASE_URL}/tools/alocar_estoque"
    payload = {
        "produto_id": "59294",
        "quantidade_total": 1000,
        "criterio": "prioridade_ruptura"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Check for 'alocacoes'
        if "alocacoes" in data and len(data["alocacoes"]) > 0:
            print(f"✅ 'alocacoes' list returned with {len(data['alocacoes'])} items.")
            print(f"   Sample: {data['alocacoes'][0]}")
        else:
            print(f"❌ 'alocacoes' field missing or empty. Response: {json.dumps(data, indent=2)}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error testing allocation: {e}")
        return False

if __name__ == "__main__":
    success_forecast = test_demand_forecast()
    success_allocation = test_allocation()
    
    if success_forecast and success_allocation:
        print("\n✅ All Tests Passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests Failed!")
        sys.exit(1)
