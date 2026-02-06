"""
Teste de Autenticação - Validação de Credenciais
Testa diferentes combinações de usuário/senha para encontrar credenciais válidas
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Lista de credenciais para testar
credentials_to_test = [
    {"username": "admin", "password": "demo123", "description": "Emergency backdoor"},
    {"username": "user@agentbi.com", "password": "user123", "description": "User fornecido"},
    {"username": "admin", "password": "admin123", "description": "Admin padrão"},
]

print("=" * 60)
print("TESTE DE AUTENTICAÇÃO - VALIDAÇÃO DE CREDENCIAIS")
print("=" * 60)

valid_token = None
valid_creds = None

for creds in credentials_to_test:
    print(f"\n🔐 Testando: {creds['username']} / {creds['password']}")
    print(f"   Descrição: {creds['description']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": creds["username"], "password": creds["password"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   ✅ SUCESSO! Token obtido: {token[:50]}...")
            valid_token = token
            valid_creds = creds
            
            # Salvar token válido
            with open("tests/test_token.txt", "w") as f:
                f.write(token)
            print(f"   ✅ Token salvo em tests/test_token.txt")
            break
        else:
            print(f"   ❌ FALHOU: {response.status_code}")
            print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"   ❌ ERRO: {e}")

print("\n" + "=" * 60)
if valid_token:
    print("✅ CREDENCIAIS VÁLIDAS ENCONTRADAS!")
    print(f"   Usuário: {valid_creds['username']}")
    print(f"   Senha: {valid_creds['password']}")
    print(f"   Token salvo para uso nos testes")
else:
    print("❌ NENHUMA CREDENCIAL VÁLIDA ENCONTRADA")
    print("   Verifique o banco de dados de usuários")
print("=" * 60)
