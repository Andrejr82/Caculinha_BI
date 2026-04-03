"""
Teste de Autenticação - Validação de Credenciais
Valida um par de credenciais informado via ambiente local
"""
import requests
import os

BASE_URL = "http://localhost:8000"

username = os.getenv("TEST_AUTH_USERNAME", "")
password = os.getenv("TEST_AUTH_PASSWORD", "")

if not username or not password:
    raise SystemExit(
        "Defina TEST_AUTH_USERNAME e TEST_AUTH_PASSWORD para validar credenciais localmente."
    )

credentials_to_test = [
    {
        "username": username,
        "password": password,
        "description": "Credenciais informadas via ambiente",
    }
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
