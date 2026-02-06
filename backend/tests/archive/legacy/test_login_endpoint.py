"""
Teste do endpoint /api/v1/auth/login diretamente
"""
import requests
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "user@agentbi.com"
TEST_PASSWORD = "user123"

print("=" * 80)
print("TESTE DO ENDPOINT /api/v1/auth/login")
print("=" * 80)

print(f"\n1. Testando login de {TEST_EMAIL} no backend...")
print(f"   URL: {BASE_URL}/api/v1/auth/login")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        },
        timeout=10
    )
    
    print(f"\n   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n   [OK] LOGIN BEM-SUCEDIDO!")
        print(f"   Token (primeiros 50 chars): {data.get('access_token', '')[:50]}...")
        
        # Decodificar token para ver claims
        import base64
        token_parts = data.get('access_token', '').split('.')
        if len(token_parts) >= 2:
            payload = token_parts[1]
            # Adicionar padding se necessario
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            print(f"\n   Claims do Token:")
            print(f"   - sub (user_id): {claims.get('sub')}")
            print(f"   - username: {claims.get('username')}")
            print(f"   - role: {claims.get('role')}")
            print(f"   - allowed_segments: {str(claims.get('allowed_segments', []))[:50]}...")
    else:
        print(f"\n   [ERRO] Login falhou!")
        print(f"   Resposta: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n   [ERRO] Nao foi possivel conectar ao backend!")
    print("   Verifique se o backend esta rodando em http://localhost:8000")
except Exception as e:
    print(f"\n   [ERRO] {e}")

print("\n" + "=" * 80)
