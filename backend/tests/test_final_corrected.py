"""
Teste Final Corrigido - Validação de Linguagem Natural
Com parser SSE correto e session_id UUID válido
"""
import requests
import json
import re
import uuid
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
print("TESTE FINAL - LINGUAGEM NATURAL (CORRIGIDO)")
print("=" * 60)

try:
    session_id = str(uuid.uuid4())  # ✅ UUID válido
    
    response = requests.get(
        f"{BASE_URL}/api/v1/chat/stream",
        params={
            "q": "Quantos produtos temos cadastrados?",
            "token": token,
            "session_id": session_id
        },
        timeout=60,
        stream=True
    )
    
    print(f"Status: {response.status_code}")
    print(f"Session ID: {session_id}")
    
    full_response = ""
    line_count = 0
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                line_str = line_str[6:]
            
            if not line_str.strip() or line_str.strip() == '[DONE]':
                continue
            
            try:
                data = json.loads(line_str)
                if 'text' in data:
                    full_response += data['text']
                line_count += 1
            except:
                pass
    
    print(f"\nLinhas processadas: {line_count}")
    print(f"Resposta capturada: {len(full_response)} chars")
    
    if len(full_response) > 0:
        print(f"Primeiros 300 chars: {full_response[:300]}...")
    
    # Validações
    is_json = full_response.strip().startswith('{')
    has_numbers = bool(re.search(r'\d+', full_response))
    has_content = len(full_response.strip()) > 50
    
    print(f"\n✅ Validações:")
    print(f"   Não é JSON: {not is_json}")
    print(f"   Tem números: {has_numbers}")
    print(f"   Tem conteúdo (>50 chars): {has_content}")
    
    if not is_json and has_numbers and has_content:
        print(f"\n🎉 TESTE PASSOU!")
        exit(0)
    else:
        print(f"\n❌ TESTE FALHOU")
        print(f"   Resposta completa: {full_response}")
        exit(1)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
