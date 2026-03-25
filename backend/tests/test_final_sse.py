"""
Teste Final - Validação de Linguagem Natural com Parser SSE Correto
"""
import requests
import json
import re
import os
from pathlib import Path
import pytest

BASE_URL = "http://localhost:8000"

pytestmark = [pytest.mark.manual, pytest.mark.external]

if os.getenv("RUN_MANUAL_SSE_TESTS", "0") != "1":
    pytest.skip(
        "teste manual SSE; defina RUN_MANUAL_SSE_TESTS=1 para executar.",
        allow_module_level=True,
    )

token_path = Path(__file__).resolve().parent / "test_token.txt"
if not token_path.exists():
    pytest.skip("teste manual SSE: token de teste não encontrado.", allow_module_level=True)

with open(token_path, "r", encoding="utf-8") as f:
    token = f.read().strip()

print("=" * 60)
print("TESTE FINAL - LINGUAGEM NATURAL")
print("=" * 60)

try:
    response = requests.get(
        f"{BASE_URL}/api/v1/chat/stream",
        params={
            "q": "Quantos produtos temos cadastrados?",  # Query real de BI
            "token": token,
            "session_id": "test_final"
        },
        timeout=60,
        stream=True
    )
    
    print(f"Status: {response.status_code}")
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                line_str = line_str[6:]
            
            if not line_str.strip() or line_str.strip() == '[DONE]':
                continue
            
            try:
                data = json.loads(line_str)
                # ✅ Campo correto é "text"
                if 'text' in data:
                    full_response += data['text']
            except:
                pass
    
    print(f"\nResposta capturada: {len(full_response)} chars")
    print(f"Conteúdo: {full_response[:200]}...")
    
    # Validações
    is_json = full_response.strip().startswith('{')
    has_numbers = bool(re.search(r'\d+', full_response))
    has_content = len(full_response.strip()) > 50
    
    print(f"\n✅ Validações:")
    print(f"   Não é JSON: {not is_json}")
    print(f"   Tem números: {has_numbers}")
    print(f"   Tem conteúdo: {has_content}")
    
    if not is_json and has_numbers and has_content:
        print(f"\n🎉 TESTE PASSOU!")
        exit(0)
    else:
        print(f"\n❌ TESTE FALHOU")
        exit(1)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
