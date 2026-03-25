#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste robusto para verificar o sistema Agent BI
Testa backend, frontend e integração
"""
import os
import requests
import time
import sys
import io
from typing import Dict, Any

import pytest

if os.getenv("RUN_SYSTEM_TESTS", "").strip().lower() not in {"1", "true", "yes", "on"}:
    pytest.skip(
        "System smoke tests disabled by default. Set RUN_SYSTEM_TESTS=1 to run.",
        allow_module_level=True,
    )

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Cores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text: str):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text: str):
    print(f"{YELLOW}⚠{RESET} {text}")

def test_backend_health() -> bool:
    """Testa se o backend está rodando e saudável"""
    print_header("TESTE 1: Backend Health Check")

    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend está rodando: {data.get('status', 'OK')}")
            return True
        else:
            print_error(f"Backend respondeu com status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Backend não está acessível: {e}")
        print_warning("Certifique-se de que o backend está rodando em http://127.0.0.1:8000")
        return False

def test_frontend_accessibility() -> bool:
    """Testa se o frontend está acessível"""
    print_header("TESTE 2: Frontend Accessibility")

    try:
        response = requests.get('http://127.0.0.1:3000', timeout=5)
        if response.status_code == 200:
            html_content = response.text

            # Verificar se tem o elemento root
            if 'id="root"' in html_content:
                print_success("Frontend está servindo o HTML correto")
            else:
                print_error("HTML do frontend não contém elemento #root")
                return False

            # Verificar se carrega o script principal
            if '/src/index.tsx' in html_content or 'index.tsx' in html_content:
                print_success("Script principal está sendo carregado")
            else:
                print_warning("Script principal pode não estar configurado corretamente")

            return True
        else:
            print_error(f"Frontend respondeu com status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Frontend não está acessível: {e}")
        print_warning("Certifique-se de que o frontend está rodando em http://127.0.0.1:3000")
        return False

def test_api_login() -> Dict[str, Any]:
    """Testa o endpoint de login da API"""
    print_header("TESTE 3: API Login")

    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/v1/auth/login',
            json={'username': 'admin', 'password': 'Admin@2024'},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print_success("Login bem-sucedido")
                print_success(f"Token recebido: {data['access_token'][:20]}...")
                return {'success': True, 'token': data['access_token']}
            else:
                print_error("Resposta não contém access_token")
                return {'success': False}
        else:
            print_error(f"Login falhou com status: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return {'success': False}
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao fazer login: {e}")
        return {'success': False}

def test_authenticated_endpoint(token: str) -> bool:
    """Testa um endpoint autenticado"""
    print_header("TESTE 4: Endpoint Autenticado (Dashboard KPIs)")

    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            'http://127.0.0.1:8000/api/v1/analytics/kpis?days=7',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Endpoint autenticado funcionando")
            print_success(f"Dados recebidos: {list(data.keys())}")
            return True
        else:
            print_error(f"Endpoint retornou status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao acessar endpoint autenticado: {e}")
        return False

def test_database_connection(token: str) -> bool:
    """Testa se a conexão com o banco de dados está funcionando"""
    print_header("TESTE 5: Database Connection (Rupturas)")

    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            'http://127.0.0.1:8000/api/v1/rupturas/summary',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Conexão com banco de dados OK")
            print_success(f"Summary: Total={data.get('total', 0)}, Críticos={data.get('criticos', 0)}")
            return True
        else:
            print_error(f"Endpoint de rupturas retornou status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao testar banco de dados: {e}")
        return False

def test_chat_endpoint(token: str) -> bool:
    """Testa o endpoint de chat"""
    print_header("TESTE 6: Chat BI Endpoint")

    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            'http://127.0.0.1:8000/api/v1/chat/query',
            json={'message': 'Quantos produtos estão em ruptura?'},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Chat endpoint funcionando")
            if 'response' in data:
                print_success(f"Resposta recebida: {data['response'][:100]}...")
            return True
        else:
            print_error(f"Chat endpoint retornou status: {response.status_code}")
            print_warning("Isso pode ser normal se o Gemini não estiver configurado")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao testar chat: {e}")
        print_warning("Isso pode ser normal se o Gemini não estiver configurado")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print(f"\n{BLUE}╔{'═'*58}╗{RESET}")
    print(f"{BLUE}║{' '*58}║{RESET}")
    print(f"{BLUE}║{'AGENT BI - TESTE ROBUSTO DO SISTEMA'.center(58)}║{RESET}")
    print(f"{BLUE}║{' '*58}║{RESET}")
    print(f"{BLUE}╚{'═'*58}╝{RESET}\n")

    results = []

    # Teste 1: Backend Health
    backend_ok = test_backend_health()
    results.append(('Backend Health', backend_ok))

    if not backend_ok:
        print_error("\n❌ Backend não está rodando. Execute 'run.bat' primeiro!\n")
        return False

    # Teste 2: Frontend
    frontend_ok = test_frontend_accessibility()
    results.append(('Frontend Accessibility', frontend_ok))

    if not frontend_ok:
        print_error("\n❌ Frontend não está acessível. Verifique se está rodando!\n")
        return False

    # Teste 3: Login
    login_result = test_api_login()
    results.append(('API Login', login_result['success']))

    if not login_result['success']:
        print_error("\n❌ Login falhou. Verifique as credenciais!\n")
        return False

    token = login_result.get('token')

    # Teste 4: Endpoint autenticado
    auth_ok = test_authenticated_endpoint(token)
    results.append(('Authenticated Endpoint', auth_ok))

    # Teste 5: Database
    db_ok = test_database_connection(token)
    results.append(('Database Connection', db_ok))

    # Teste 6: Chat
    chat_ok = test_chat_endpoint(token)
    results.append(('Chat Endpoint', chat_ok))

    # Resumo
    print_header("RESUMO DOS TESTES")

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for test_name, ok in results:
        if ok:
            print_success(f"{test_name:<30} PASSOU")
        else:
            print_error(f"{test_name:<30} FALHOU")

    print(f"\n{BLUE}{'='*60}{RESET}")

    if passed == total:
        print(f"{GREEN}✓ TODOS OS TESTES PASSARAM ({passed}/{total}){RESET}")
        print(f"\n{GREEN}🎉 Sistema está funcionando perfeitamente!{RESET}")
        print(f"\n{BLUE}Acesse: http://localhost:3000{RESET}")
        print(f"{BLUE}Login: admin / Admin@2024{RESET}\n")
        return True
    else:
        print(f"{YELLOW}⚠ {passed}/{total} TESTES PASSARAM{RESET}")

        if passed >= 4:
            print(f"\n{YELLOW}Sistema está parcialmente funcional.{RESET}")
            print(f"{BLUE}Acesse: http://localhost:3000{RESET}")
            print(f"{BLUE}Login: admin / Admin@2024{RESET}\n")
        else:
            print(f"\n{RED}❌ Sistema não está funcionando corretamente.{RESET}\n")

        return False

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Testes interrompidos pelo usuário.{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Erro inesperado: {e}{RESET}\n")
        sys.exit(1)
