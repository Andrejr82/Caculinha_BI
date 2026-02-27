"""
Teste de Diagnóstico - Configuração Tool Config
Verifica se o LLM está recebendo ferramentas corretamente
"""
import requests
import json
import uuid
from pathlib import Path
import pytest

BASE_URL = "http://localhost:8000"

# Ler token válido (teste de integração manual)
token_path = Path("tests/test_token.txt")
if not token_path.exists():
    pytest.skip("teste manual: tests/test_token.txt não encontrado", allow_module_level=True)

with open(token_path, "r", encoding="utf-8") as f:
    token = f.read().strip()

print("=" * 60)
print("DIAGNÓSTICO: CONFIGURAÇÃO DE FERRAMENTAS")
print("=" * 60)

# Teste 1: Query simples de dados (deve chamar ferramenta)
queries = [
    ("Analise vendas do produto 25 em todas as lojas", "analisar_produto_todas_lojas"),
    ("Quantos produtos temos cadastrados?", "consultar_dados_flexivel"),
    ("Crie um gráfico de vendas", "gerar_grafico_universal_v2"),
]

for query, expected_tool in queries:
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print(f"Ferramenta esperada: {expected_tool}")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/chat/stream",
            params={
                "q": query,
                "token": token,
                "session_id": session_id
            },
            timeout=60,
            stream=True
        )
        
        tools_called = []
        response_text = ""
        
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
                        response_text += data['text']
                    
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            tool_name = tc.get('function', {}).get('name', 'unknown')
                            tools_called.append(tool_name)
                            print(f"  🔧 Ferramenta chamada: {tool_name}")
                except:
                    pass
        
        if not tools_called:
            print(f"  ❌ NENHUMA ferramenta chamada!")
            print(f"  Resposta: {response_text[:200]}...")
        elif expected_tool in tools_called:
            print(f"  ✅ Ferramenta correta chamada!")
        else:
            print(f"  ⚠️ Ferramenta incorreta: {tools_called}")
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")

print(f"\n{'=' * 60}")
print("FIM DO DIAGNÓSTICO")
print("=" * 60)
