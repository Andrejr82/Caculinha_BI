import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def get_token():
    # Login as admin (default creds)
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@2024"
        })
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
        return resp.json()["access_token"]
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def ask(query, token):
    print(f"\n[USER]: {query}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Use legacy endpoint for simplicity of testing content
        resp = requests.post(
            f"{BASE_URL}/api/v1/chat", 
            json={"query": query},
            headers=headers
        )
        if resp.status_code == 200:
            data = resp.json()
            # Parse the inner response string or object
            # The endpoint returns {"response": str(...), "full_agent_response": dict}
            full_resp = data.get("full_agent_response", {})
            result = full_resp.get("result", "")
            
            # If result is a dict (tool output), print formatted
            if isinstance(result, dict):
                print(f"[AGENT - TOOL]: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                print(f"[AGENT]: {result}")
                
            # Check for chart
            if full_resp.get("chart_spec"):
                print("[AGENT]: (Chart Specification Generated)")
        else:
            print(f"[ERROR]: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[EXCEPTION]: {e}")

def main():
    print("--- Autenticando ---")
    token = get_token()
    print("--- Iniciando Bateria de Testes do Mundo Real ---")
    
    # 1. Básica: Contagem/Filtro
    ask("Quantos produtos diferentes temos no segmento PAPELARIA?", token)
    
    # 2. Média: Agregação e Ordenação
    ask("Qual o fabricante que mais vendeu (VENDA_30DD) no total?", token)
    
    # 3. Complexa: Comparação
    ask("Compare as vendas (VENDA_30DD) entre a UNE 1 e a UNE 2365 para o segmento TECIDOS.", token)
    
    # 4. Gráfico: Visualização
    ask("Gere um gráfico de barras dos top 5 fabricantes com maior estoque no CD.", token)

if __name__ == "__main__":
    main()
