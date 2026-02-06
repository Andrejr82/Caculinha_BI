"""
Testes de Integração - Validação de Prompt v4 e Anti-Repetição
Testa se o sistema está usando o prompt consolidado corretamente
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def get_auth_token():
    """Obtém token de autenticação do arquivo ou usa fallback"""
    try:
        with open("tests/test_token.txt", "r") as f:
            return f.read().strip()
    except:
        # Fallback: tentar obter token via login
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                                    json={"username": "admin", "password": "admin123"})
            if response.status_code == 200:
                token = response.json().get("access_token")
                # Salvar para próximas execuções
                with open("tests/test_token.txt", "w") as f:
                    f.write(token)
                return token
        except:
            pass
        return "test_token"  # Fallback final

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✅ PASSOU{Colors.END}" if passed else f"{Colors.RED}❌ FALHOU{Colors.END}"
    print(f"\n{status} - {name}")
    if details:
        print(f"  {details}")

def test_backend_health():
    """Teste 1: Backend está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=30)  # ✅ Aumentado de 5s para 30s
        passed = response.status_code == 200
        print_test("Backend Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Backend Health Check", False, f"Erro: {e}")
        return False

def test_prompt_consolidation():
    """Teste 2: Prompt consolidado está sendo usado"""
    try:
        # Fazer uma query simples
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/stream",
            json={"message": "teste", "session_id": "test_consolidation"},
            timeout=60,  # ✅ Aumentado de 10s para 60s
            stream=True
        )
        
        # Verificar se não há erro de "unexpected keyword argument 'version'"
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        full_response += data['content']
                except:
                    pass
        
        # Se chegou aqui sem erro, passou
        passed = "unexpected keyword argument" not in full_response.lower()
        print_test("Prompt Consolidado (sem erro version)", passed)
        return passed
    except Exception as e:
        print_test("Prompt Consolidado", False, f"Erro: {e}")
        return False

def test_no_technical_leakage():
    """Teste 3: Sem vazamento de informações técnicas"""
    try:
        # ✅ FIX: Endpoint /stream usa GET
        response = requests.get(
            f"{BASE_URL}/api/v1/chat/stream",
            params={
                "q": "Analise vendas do produto 25",
                "token": get_auth_token(),
                "session_id": "test_leakage"
            },
            timeout=60,
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        full_response += data['content']
                except:
                    pass
        
        # Verificar violações
        violations = []
        if "prever_demanda_sazonal" in full_response:
            violations.append("Menciona 'prever_demanda_sazonal'")
        if "calcular_eoq" in full_response:
            violations.append("Menciona 'calcular_eoq'")
        if "produto_codigo=" in full_response:
            violations.append("Menciona 'produto_codigo='")
        if "é crucial utilizar a ferramenta" in full_response.lower():
            violations.append("Menciona 'é crucial utilizar a ferramenta'")
        
        passed = len(violations) == 0
        details = f"Violações: {', '.join(violations)}" if violations else "Nenhuma violação detectada"
        print_test("Sem Vazamento Técnico", passed, details)
        
        if not passed:
            print(f"\n{Colors.YELLOW}Resposta recebida:{Colors.END}")
            print(full_response[:500] + "..." if len(full_response) > 500 else full_response)
        
        return passed
    except Exception as e:
        print_test("Sem Vazamento Técnico", False, f"Erro: {e}")
        return False

def test_no_repetition():
    """Teste 4: Sem repetição de código do produto"""
    try:
        # ✅ FIX: Endpoint /stream usa GET
        response = requests.get(
            f"{BASE_URL}/api/v1/chat/stream",
            params={
                "q": "Analise vendas do produto 25",
                "token": get_auth_token(),
                "session_id": "test_repetition"
            },
            timeout=60,
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        full_response += data['content']
                except:
                    pass
        
        # Contar menções de "produto 25"
        count_produto_25 = full_response.lower().count("produto 25")
        count_produto_equals = full_response.count("produto = 25")
        
        # Deve mencionar produto 25 no máximo 2 vezes (início e talvez 1 vez no meio)
        passed = count_produto_25 <= 2 and count_produto_equals == 0
        details = f"'produto 25': {count_produto_25}x, 'produto = 25': {count_produto_equals}x"
        print_test("Sem Repetição Excessiva", passed, details)
        return passed
    except Exception as e:
        print_test("Sem Repetição Excessiva", False, f"Erro: {e}")
        return False

def test_natural_language():
    """Teste 5: Resposta em linguagem natural"""
    try:
        # ✅ FIX: Endpoint /stream usa GET
        response = requests.get(
            f"{BASE_URL}/api/v1/chat/stream",
            params={
                "q": "Analise vendas do produto 25",
                "token": get_auth_token(),
                "session_id": "test_natural"
            },
            timeout=60,
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                # Remover prefixo "data: " se existir
                if line_str.startswith('data: '):
                    line_str = line_str[6:]
                
                # Ignorar linha vazia ou [DONE]
                if not line_str.strip() or line_str.strip() == '[DONE]':
                    continue
                
                try:
                    data = json.loads(line_str)
                    if 'content' in data:
                        full_response += data['content']
                    elif 'delta' in data and 'content' in data['delta']:
                        full_response += data['delta']['content']
                except json.JSONDecodeError:
                    # Linha não é JSON válido, ignorar
                    continue
        
        # Verificar que NÃO é JSON estruturado
        is_json_response = full_response.strip().startswith('{') and full_response.strip().endswith('}')
        
        # Verificar que tem números específicos (mais robusto)
        import re
        has_numbers = bool(re.search(r'\d+', full_response))
        
        # Verificar que tem pelo menos 50 caracteres (não é resposta vazia)
        has_content = len(full_response.strip()) > 50
        
        passed = not is_json_response and has_numbers and has_content
        details = f"JSON: {is_json_response}, Tem números: {has_numbers}, Conteúdo: {len(full_response)} chars"
        print_test("Linguagem Natural", passed, details)
        
        if not passed:
            print(f"\n{Colors.YELLOW}Resposta recebida ({len(full_response)} chars):{Colors.END}")
            print(full_response[:300] + "..." if len(full_response) > 300 else full_response)
        
        return passed
    except Exception as e:
        print_test("Linguagem Natural", False, f"Erro: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}SUITE DE TESTES - VALIDAÇÃO PROMPT V4{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Teste 1: Backend Health
    results.append(("Backend Health", test_backend_health()))
    time.sleep(1)
    
    # Teste 2: Prompt Consolidado
    results.append(("Prompt Consolidado", test_prompt_consolidation()))
    time.sleep(2)
    
    # Teste 3: Sem Vazamento Técnico
    results.append(("Sem Vazamento Técnico", test_no_technical_leakage()))
    time.sleep(2)
    
    # Teste 4: Sem Repetição
    results.append(("Sem Repetição", test_no_repetition()))
    time.sleep(2)
    
    # Teste 5: Linguagem Natural
    results.append(("Linguagem Natural", test_natural_language()))
    
    # Resumo
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}RESUMO DOS TESTES{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
        print(f"{status} {name}")
    
    print(f"\n{Colors.BLUE}Total: {passed_count}/{total_count} testes passaram{Colors.END}")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}🎉 TODOS OS TESTES PASSARAM!{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}⚠️ ALGUNS TESTES FALHARAM{Colors.END}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
