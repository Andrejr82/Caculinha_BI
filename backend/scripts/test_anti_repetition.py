"""
Script de teste para validar correção de respostas repetitivas
Testa o produto 25 com duas perguntas diferentes
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/v1/chat/stream"

# Credenciais de teste (ajustar conforme necessário)
TEST_TOKEN = "your_test_token_here"  # TODO: Obter token real
SESSION_ID = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def test_repetitive_responses():
    """
    Testa se respostas para perguntas diferentes sobre o mesmo produto são diferentes
    """
    print("="*80)
    print("TESTE DE RESPOSTAS REPETITIVAS - PRODUTO 25")
    print("="*80)
    print(f"Session ID: {SESSION_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Pergunta 1: Análise de vendas
    query1 = "Analise vendas do produto 25 em todas as lojas"
    print(f"📝 PERGUNTA 1: {query1}")
    print("-" * 80)
    
    try:
        # TODO: Implementar chamada SSE real
        # Por enquanto, apenas documentar o teste manual
        print("⚠️ Este teste requer execução manual via frontend ou curl")
        print()
        print("INSTRUÇÕES PARA TESTE MANUAL:")
        print("1. Abra o frontend em http://localhost:3000")
        print("2. Faça login")
        print("3. No chat, digite:")
        print(f"   '{query1}'")
        print("4. Aguarde a resposta completa")
        print("5. Copie a resposta e salve como 'resposta1.txt'")
        print()
        
        # Pergunta 2: Quantidade para demanda
        query2 = "Qual a quantidade de unidades real para atender a demanda de vendas do produto 25?"
        print(f"📝 PERGUNTA 2: {query2}")
        print("-" * 80)
        print("6. No mesmo chat, digite:")
        print(f"   '{query2}'")
        print("7. Aguarde a resposta completa")
        print("8. Copie a resposta e salve como 'resposta2.txt'")
        print()
        
        print("="*80)
        print("CRITÉRIOS DE VALIDAÇÃO:")
        print("="*80)
        print("✅ PASSOU se:")
        print("  - Resposta 1 foca em VENDAS PASSADAS (faturamento, distribuição)")
        print("  - Resposta 2 foca em PREVISÃO FUTURA (estoque, EOQ, demanda)")
        print("  - As respostas são DIFERENTES (não há cópia)")
        print("  - Ambas contêm NÚMEROS ESPECÍFICOS")
        print()
        print("❌ FALHOU se:")
        print("  - Resposta 2 repete informações da Resposta 1")
        print("  - Respostas são genéricas sem números específicos")
        print("  - Ambas têm estrutura/conteúdo muito similar")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    return True

def check_backend_status():
    """Verifica se o backend está rodando"""
    print("🔍 Verificando status do backend...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está rodando!")
            return True
        else:
            print(f"⚠️ Backend respondeu com status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend não está rodando!")
        print("   Execute: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar backend: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTE DE VALIDAÇÃO - PROMPT V4 ANTI-REPETIÇÃO")
    print("="*80)
    print()
    
    # Verificar backend
    if not check_backend_status():
        print("\n⚠️ Inicie o backend primeiro!")
        exit(1)
    
    print()
    
    # Executar teste
    test_repetitive_responses()
    
    print()
    print("="*80)
    print("PRÓXIMOS PASSOS:")
    print("="*80)
    print("1. Execute o teste manual conforme instruções acima")
    print("2. Compare as duas respostas")
    print("3. Valide se atendem aos critérios de sucesso")
    print("4. Reporte os resultados")
    print("="*80)
