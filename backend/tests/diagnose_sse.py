"""
Teste de Captura SSE - Diagnóstico de Formato de Resposta
Captura resposta real do endpoint SSE para entender o formato
"""
import requests
import time

BASE_URL = "http://localhost:8000"

# Ler token válido
with open("tests/test_token.txt", "r") as f:
    token = f.read().strip()

print("=" * 60)
print("TESTE DE CAPTURA SSE - DIAGNÓSTICO")
print("=" * 60)
print(f"Token: {token[:50]}...")

try:
    response = requests.get(
        f"{BASE_URL}/api/v1/chat/stream",
        params={
            "q": "teste",
            "token": token,
            "session_id": "debug_sse_test"
        },
        stream=True,
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\n" + "=" * 60)
    print("RESPOSTA RAW (primeiras 20 linhas):")
    print("=" * 60)
    
    line_count = 0
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            print(f"Linha {line_count}: {repr(line_str)}")
            line_count += 1
            if line_count >= 20:
                break
    
    print("\n" + "=" * 60)
    print(f"Total de linhas capturadas: {line_count}")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
