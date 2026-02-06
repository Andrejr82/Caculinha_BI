import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_create_user():
    print("🚀 Iniciando teste de criação de usuário...")
    
    # 1. Login como Admin (Backdoor)
    print("\n🔑 Tentando login como Admin...")
    login_data = {
        "username": "admin",
        "password": "demo123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Falha no login: {response.status_code}")
            print(response.text)
            return
        
        token = response.json()["access_token"]
        print("✅ Login sucesso! Token obtido.")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
    except Exception as e:
        print(f"❌ Erro de conexão no login: {e}")
        return

    # 2. Criar Usuário (Teste)
    print("\n👤 Tentando criar usuário de teste...")
    new_user = {
        "username": "testuser_debug",
        "email": "test_debug@example.com",
        "password": "Password123!",
        "role": "user",
        "allowed_segments": ["*"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/admin/users", json=new_user, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ Usuário criado com sucesso!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Falha ao criar usuário: {response.status_code}")
            print(f"Detalhe: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão ao criar usuário: {e}")

if __name__ == "__main__":
    test_create_user()
