"""Testar login via API"""
import requests
import json

url = "http://localhost:8000/api/v1/auth/login"
data = {
    "username": "admin",
    "password": "admin123"
}

print("🔐 Testando login...")
print(f"URL: {url}")
print(f"Dados: {data}\n")

try:
    response = requests.post(url, json=data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}\n")
    
    if response.status_code == 200:
        print("✅ LOGIN FUNCIONOU!")
        result = response.json()
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
    else:
        print("❌ LOGIN FALHOU!")
        print(f"Erro: {response.json()}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERRO: Backend não está respondendo!")
    print("   Verifique se o backend está rodando na porta 8000")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
