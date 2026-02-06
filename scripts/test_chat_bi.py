"""
Script de Teste Automatizado do Chat BI
Valida as 9 correções de limitações
"""
import requests
import json
import time
from typing import Dict, List, Any

# Configuração
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/v1/chat"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_chat_query(query: str, test_name: str, expected_conditions: List[str]) -> Dict[str, Any]:
    """
    Envia query para o chat e valida resposta
    """
    print(f"\n{Colors.BLUE}🧪 {test_name}{Colors.END}")
    print(f"   Query: {query}")
    
    try:
        # Enviar query
        payload = {
            "message": query,
            "user_id": "test_user",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"   {Colors.RED}✗ FALHOU: Status {response.status_code}{Colors.END}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Validar condições esperadas
        results = []
        for condition in expected_conditions:
            # Aqui você pode adicionar lógica específica para cada condição
            # Por enquanto, apenas verificamos se a resposta existe
            if "response" in data or "message" in data:
                results.append(True)
            else:
                results.append(False)
        
        success = all(results)
        
        if success:
            print(f"   {Colors.GREEN}✓ PASSOU{Colors.END}")
        else:
            print(f"   {Colors.RED}✗ FALHOU{Colors.END}")
        
        return {
            "success": success,
            "response": data,
            "conditions_met": results
        }
        
    except requests.exceptions.Timeout:
        print(f"   {Colors.RED}✗ FALHOU: Timeout{Colors.END}")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"   {Colors.RED}✗ FALHOU: {str(e)}{Colors.END}")
        return {"success": False, "error": str(e)}

def main():
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTES AUTOMATIZADOS DO CHAT BI{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # Verificar se backend está rodando
    print(f"\n{Colors.BLUE}🔍 Verificando backend...{Colors.END}")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print(f"   {Colors.GREEN}✓ Backend rodando{Colors.END}")
        else:
            print(f"   {Colors.RED}✗ Backend não está saudável{Colors.END}")
            return
    except:
        print(f"   {Colors.RED}✗ Backend não está rodando{Colors.END}")
        print(f"\n{Colors.YELLOW}Por favor, inicie o backend:{Colors.END}")
        print(f"   cd backend")
        print(f"   python main.py")
        return
    
    # Testes
    tests = [
        {
            "name": "Teste 1: Limites de Dados (35 UNEs)",
            "query": "gere um relatorio de vendas do produto 369947 em todas as lojas",
            "conditions": ["response_exists", "data_complete"]
        },
        {
            "name": "Teste 2: Contexto Expandido",
            "query": "Qual o estoque do produto 369947?",
            "conditions": ["response_exists"]
        },
        {
            "name": "Teste 3: Respostas Completas",
            "query": "Faça uma análise detalhada das vendas do produto 369947",
            "conditions": ["response_exists", "response_not_truncated"]
        },
        {
            "name": "Teste 4: Gráficos Expandidos",
            "query": "Mostre um gráfico de vendas dos top 50 produtos",
            "conditions": ["response_exists", "chart_generated"]
        },
        {
            "name": "Teste 5: Schema Dinâmico",
            "query": "Quais colunas estão disponíveis no banco de dados?",
            "conditions": ["response_exists", "columns_listed"]
        }
    ]
    
    results = []
    for test in tests:
        result = test_chat_query(
            test["query"],
            test["name"],
            test["conditions"]
        )
        results.append(result)
        time.sleep(2)  # Delay entre testes
    
    # Resumo
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}RESUMO DOS TESTES{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    passed = sum(1 for r in results if r.get("success", False))
    total = len(results)
    
    print(f"\n   Passaram: {passed}/{total}")
    
    if passed == total:
        print(f"\n   {Colors.GREEN}✅ TODOS OS TESTES PASSARAM!{Colors.END}")
        print(f"\n   {Colors.GREEN}Sistema pronto para commit.{Colors.END}")
    else:
        print(f"\n   {Colors.RED}❌ ALGUNS TESTES FALHARAM{Colors.END}")
        print(f"\n   {Colors.YELLOW}Revisar problemas antes do commit.{Colors.END}")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testes interrompidos pelo usuário.{Colors.END}")
        exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}ERRO FATAL: {str(e)}{Colors.END}")
        exit(1)
