"""
Teste de Seleção de Ferramenta - Análise de Todas as Lojas
Valida se o LLM seleciona analisar_produto_todas_lojas quando deveria
"""
import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

# Ler token válido
with open("tests/test_token.txt", "r") as f:
    token = f.read().strip()

print("=" * 60)
print("TESTE: SELEÇÃO DE FERRAMENTA - TODAS AS LOJAS")
print("=" * 60)

session_id = str(uuid.uuid4())

try:
    response = requests.get(
        f"{BASE_URL}/api/v1/chat/stream",
        params={
            "q": "Analise vendas do produto 25 em todas as lojas",
            "token": token,
            "session_id": session_id
        },
        timeout=60,
        stream=True
    )
    
    print(f"Status: {response.status_code}")
    print(f"Session ID: {session_id}")
    
    full_response = ""
    tool_calls_detected = []
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                line_str = line_str[6:]
            
            if not line_str.strip() or line_str.strip() == '[DONE]':
                continue
            
            try:
                data = json.loads(line_str)
                
                # Capturar texto da resposta
                if 'text' in data:
                    full_response += data['text']
                
                # Detectar chamadas de ferramentas
                if 'tool_calls' in data:
                    for tool_call in data['tool_calls']:
                        tool_name = tool_call.get('function', {}).get('name', 'unknown')
                        tool_calls_detected.append(tool_name)
                        print(f"\n🔧 Ferramenta detectada: {tool_name}")
                
            except:
                pass
    
    print(f"\n{'=' * 60}")
    print("RESULTADO:")
    print("=" * 60)
    
    print(f"\nFerramentas chamadas: {tool_calls_detected}")
    print(f"Resposta ({len(full_response)} chars): {full_response[:300]}...")
    
    # Validações
    print(f"\n{'=' * 60}")
    print("VALIDAÇÕES:")
    print("=" * 60)
    
    # Verificar se usou a ferramenta correta
    used_correct_tool = 'analisar_produto_todas_lojas' in tool_calls_detected
    print(f"✅ Usou analisar_produto_todas_lojas: {used_correct_tool}")
    
    # Verificar se NÃO focou em apenas uma loja
    focused_on_single_store = "1685" in full_response and full_response.count("1685") > 2
    print(f"✅ NÃO focou apenas na UNE 1685: {not focused_on_single_store}")
    
    # Verificar se mencionou múltiplas lojas
    mentions_multiple_stores = any(word in full_response.lower() for word in ["lojas", "todas", "rede", "distribuição"])
    print(f"✅ Menciona múltiplas lojas: {mentions_multiple_stores}")
    
    # Verificar se tem números agregados
    has_totals = any(word in full_response.lower() for word in ["total", "soma", "consolidado", "todas as lojas"])
    print(f"✅ Tem totais/agregações: {has_totals}")
    
    print(f"\n{'=' * 60}")
    
    if used_correct_tool and not focused_on_single_store and mentions_multiple_stores:
        print("🎉 TESTE PASSOU!")
        print("LLM selecionou a ferramenta correta e analisou todas as lojas")
        exit(0)
    else:
        print("❌ TESTE FALHOU!")
        if not used_correct_tool:
            print("  - LLM não usou analisar_produto_todas_lojas")
            print(f"  - Ferramentas usadas: {tool_calls_detected}")
        if focused_on_single_store:
            print("  - Resposta focou apenas na UNE 1685")
        if not mentions_multiple_stores:
            print("  - Resposta não menciona múltiplas lojas")
        exit(1)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
