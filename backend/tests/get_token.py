"""
Script para obter token de autenticação válido para testes
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Tentar login com credenciais de teste
login_data = {
    "username": "admin",
    "password": "admin123"
}

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
