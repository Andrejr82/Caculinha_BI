"""
Test Login Flow - Live Test Script

Testa o fluxo de login contra o backend em execução.
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    print("=" * 60)
    print("🔐 Teste de Login")
    print("=" * 60)
    
    # Test 1: Valid Supabase user (if configured)
    credentials = [
        {"username": "admin@lojas-cacula.com.br", "password": "123456"},
        {"username": "andre.junior@cacula.com.br", "password": "admin123"},
        {"username": "test@test.com", "password": "test123"},
    ]
    
    for cred in credentials:
        print(f"\n📧 Testando: {cred['username']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=cred,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ LOGIN SUCESSO!")
                print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"   Role: {data.get('role', 'N/A')}")
                return True
            elif response.status_code == 401:
                print(f"   ❌ Credenciais inválidas")
                try:
                    detail = response.json().get("detail", "")
                    print(f"   Detalhe: {detail}")
                except:
                    pass
            elif response.status_code == 404:
                print(f"   ❌ ROTA NÃO ENCONTRADA (404)")
                return False
            else:
                print(f"   ⚠️ Resposta: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ ERRO: Backend não está rodando em {BASE_URL}")
            return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("⚠️ Nenhum login bem-sucedido.")
    print("Verifique se você tem usuários cadastrados no Supabase.")
    print("=" * 60)
    return False


if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)
