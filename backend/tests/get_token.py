"""
Script para obter token de autenticação válido para testes
"""
import requests
import os

BASE_URL = "http://localhost:8000"

# Credenciais fornecidas pelo ambiente local
login_data = {
    "username": os.getenv("TEST_AUTH_USERNAME", ""),
    "password": os.getenv("TEST_AUTH_PASSWORD", "")
}

if not login_data["username"] or not login_data["password"]:
    raise SystemExit(
        "Defina TEST_AUTH_USERNAME e TEST_AUTH_PASSWORD para gerar tests/test_token.txt localmente."
    )

try:
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ Token obtido: {token[:50]}...")
        
        # Salvar token para uso nos testes
        with open("tests/test_token.txt", "w") as f:
            f.write(token)
        print("✅ Token salvo em tests/test_token.txt")
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Erro: {e}")
