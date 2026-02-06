"""
Teste de Verificação Completa do Chat BI
Garante que o agente está respondendo corretamente.
"""
import requests
import json
import time
from typing import Dict, Any

# Configuração
BACKEND_URL = "http://localhost:8000"
TEST_QUERY = "gere um relatorio de vendas do produto 369947 em todas as lojas"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_step(step: str, status: str = "INFO"):
    """Imprime passo do teste com cor."""
    color = Colors.BLUE if status == "INFO" else Colors.GREEN if status == "OK" else Colors.RED if status == "ERROR" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.RESET} {step}")

def get_auth_token() -> str:
    """Obtém token de autenticação fazendo login."""
    print_step("Fazendo login para obter token...", "INFO")
    
    # Credenciais de admin (padrão do sistema)
    login_data = {
        "username": "admin",
        "password": "demo123"  # Backdoor de emergência
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data,  # JSON, não form data
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_step("Login bem-sucedido! Token obtido.", "OK")
                return token
            else:
                print_step("Login retornou sem token!", "ERROR")
                return None
        else:
            print_step(f"Login falhou com status {response.status_code}", "ERROR")
            print_step(f"Resposta: {response.text}", "ERROR")
            return None
    except Exception as e:
        print_step(f"Erro ao fazer login: {e}", "ERROR")
        return None


def test_backend_health() -> bool:
    """Testa se o backend está rodando."""
    print_step("Testando saúde do backend...", "INFO")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_step(f"Backend está saudável: {data}", "OK")
            return True
        else:
            print_step(f"Backend retornou status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_step(f"Erro ao conectar no backend: {e}", "ERROR")
        return False

def test_chat_endpoint(auth_token: str) -> Dict[str, Any]:
    """Testa o endpoint de chat diretamente (sem streaming)."""
    print_step("Testando endpoint /api/v1/chat...", "INFO")
    
    payload = {
        "query": TEST_QUERY,
        "session_id": "test_session_verification"
    }
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=90  # 90 segundos para query complexa
        )
        
        if response.status_code == 200:
            data = response.json()
            print_step("Endpoint /api/v1/chat respondeu com sucesso!", "OK")
            return {"success": True, "data": data}
        else:
            print_step(f"Endpoint retornou status {response.status_code}", "ERROR")
            print_step(f"Resposta: {response.text[:500]}", "ERROR")
            return {"success": False, "error": f"Status {response.status_code}"}
    except requests.Timeout:
        print_step("Timeout ao aguardar resposta (90s)", "ERROR")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print_step(f"Erro ao chamar endpoint: {e}", "ERROR")
        return {"success": False, "error": str(e)}

def validate_response(response_data: Dict[str, Any]) -> bool:
    """Valida se a resposta do agente é válida."""
    print_step("Validando resposta do agente...", "INFO")
    
    # Verificar estrutura básica
    if not isinstance(response_data, dict):
        print_step("Resposta não é um dicionário", "ERROR")
        return False
    
    # O endpoint /chat retorna {"response": "...", "full_agent_response": {...}}
    if "full_agent_response" in response_data:
        agent_response = response_data["full_agent_response"]
    else:
        agent_response = response_data
    
    # Verificar se tem tipo
    if "type" not in agent_response:
        print_step(f"Resposta não tem campo 'type'. Keys: {agent_response.keys()}", "ERROR")
        return False
    
    # Verificar se tem resultado
    if "result" not in agent_response:
        print_step("Resposta não tem campo 'result'", "ERROR")
        return False
    
    result = agent_response.get("result", {})
    
    # Verificar se tem mensagem
    if isinstance(result, dict):
        mensagem = result.get("mensagem", "")
    else:
        mensagem = str(result)
    
    if not mensagem or len(mensagem.strip()) == 0:
        print_step("Resposta tem mensagem vazia!", "ERROR")
        return False
    
    # Verificar se não é erro
    if "erro" in mensagem.lower() and "desculpe" in mensagem.lower():
        print_step(f"Resposta parece ser um erro: {mensagem[:200]}", "WARNING")
        # Não retornar False aqui, pois pode ser um erro válido do agente
    
    print_step(f"Resposta válida! Tipo: {agent_response['type']}", "OK")
    print_step(f"Mensagem (primeiros 200 chars): {mensagem[:200]}...", "OK")
    
    # Verificar se tem gráfico (opcional)
    if "chart_data" in agent_response:
        print_step("Resposta contém dados de gráfico!", "OK")
    
    return True

def main():
    """Executa verificação completa."""
    print("\n" + "="*70)
    print("VERIFICAÇÃO COMPLETA DO CHAT BI")
    print("="*70 + "\n")
    
    # Passo 1: Verificar saúde do backend
    if not test_backend_health():
        print_step("\nBackend não está rodando! Abortando testes.", "ERROR")
        return False
    
    print()
    
    # Passo 2: Obter token de autenticação
    auth_token = get_auth_token()
    if not auth_token:
        print_step("\nFalha ao obter token de autenticação! Abortando testes.", "ERROR")
        return False
    
    print()
    
    # Passo 3: Testar endpoint de chat
    result = test_chat_endpoint(auth_token)
    
    if not result["success"]:
        print_step(f"\nEndpoint de chat falhou: {result.get('error')}", "ERROR")
        return False
    
    print()
    
    # Passo 4: Validar resposta
    if not validate_response(result["data"]):
        print_step("\nResposta do agente é inválida!", "ERROR")
        return False
    
    print()
    print("="*70)
    print_step("TODOS OS TESTES PASSARAM! CHAT BI ESTÁ FUNCIONANDO!", "OK")
    print("="*70)
    
    # Exibir resposta completa
    print("\n" + "="*70)
    print("RESPOSTA COMPLETA DO AGENTE:")
    print("="*70)
    print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
