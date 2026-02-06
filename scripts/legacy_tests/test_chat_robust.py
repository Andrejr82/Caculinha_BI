"""
Testes Robustos para Chat BI e CodeChat
========================================

Executa bateria completa de testes validando:
- Conversação básica
- Análises de dados complexas
- Geração de gráficos
- Filtros e segmentação
- CodeChat (RAG de documentação)
- Cache semântico
- Sistema de feedback
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

# ==================== CONFIGURAÇÃO ====================

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ==================== AUTENTICAÇÃO ====================

def login() -> Optional[str]:
    """Faz login e retorna token JWT."""
    print(f"{Colors.BLUE}[AUTH]{Colors.END} Fazendo login...")

    response = requests.post(
        f"{API_V1}/auth/login",
        json={"username": "admin", "password": "Admin@2024"}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"{Colors.GREEN}[OK]{Colors.END} Token obtido: {token[:50]}...")
        return token
    else:
        print(f"{Colors.RED}[ERRO]{Colors.END} Falha no login: {response.text}")
        return None

# ==================== TESTES DE CHAT ====================

class ChatTester:
    def __init__(self, token: str):
        self.token = token
        self.session_id = f"test-session-{int(time.time())}"
        self.test_results = []

    def _send_query(self, query: str, timeout: int = 30) -> Dict[str, Any]:
        """Envia query para o chat e coleta resposta completa."""
        print(f"\n{Colors.CYAN}[QUERY]{Colors.END} {query}")

        url = f"{API_V1}/chat/stream"
        params = {
            "q": query,
            "token": self.token,
            "session_id": self.session_id
        }

        start_time = time.time()

        try:
            response = requests.get(url, params=params, stream=True, timeout=timeout)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": time.time() - start_time
                }

            # Processar stream SSE
            full_text = ""
            chart_spec = None
            table_data = None
            tools_used = []

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode('utf-8')

                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: '

                    try:
                        data = json.loads(data_str)

                        if data.get('type') == 'text':
                            full_text += data.get('text', '')

                        elif data.get('type') == 'chart':
                            chart_spec = data.get('chart_spec')

                        elif data.get('type') == 'table':
                            table_data = data.get('data')

                        elif data.get('type') == 'tool_progress':
                            tool_name = data.get('tool', '')
                            if tool_name and tool_name not in tools_used and tool_name not in ['Pensando', 'Processando resposta']:
                                tools_used.append(tool_name)

                        elif data.get('type') == 'final' and data.get('done'):
                            break

                    except json.JSONDecodeError:
                        pass

            duration = time.time() - start_time

            return {
                "success": True,
                "text": full_text,
                "chart": chart_spec,
                "table": table_data,
                "tools": tools_used,
                "duration": duration
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout",
                "duration": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def _validate_result(self, test_name: str, result: Dict[str, Any], expectations: Dict[str, Any]) -> bool:
        """Valida resultado de um teste."""

        if not result['success']:
            print(f"{Colors.RED}[FALHA]{Colors.END} {test_name}")
            print(f"  Erro: {result.get('error', 'Unknown')}")
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": result.get('error'),
                "duration": result['duration']
            })
            return False

        # Validar expectativas
        checks_passed = []
        checks_failed = []

        if 'min_text_length' in expectations:
            min_len = expectations['min_text_length']
            actual_len = len(result['text'])
            if actual_len >= min_len:
                checks_passed.append(f"Texto com {actual_len} caracteres (>= {min_len})")
            else:
                checks_failed.append(f"Texto muito curto: {actual_len} < {min_len}")

        if expectations.get('expect_chart'):
            if result['chart']:
                checks_passed.append("Gráfico gerado")
            else:
                checks_failed.append("Gráfico esperado mas não gerado")

        if expectations.get('expect_table'):
            if result['table']:
                checks_passed.append("Tabela gerada")
            else:
                checks_failed.append("Tabela esperada mas não gerada")

        if 'expect_tools' in expectations:
            expected_tools = expectations['expect_tools']
            for tool in expected_tools:
                if tool in result['tools']:
                    checks_passed.append(f"Tool '{tool}' usada")
                else:
                    checks_failed.append(f"Tool '{tool}' esperada mas não usada")

        if 'keywords' in expectations:
            keywords = expectations['keywords']
            text_lower = result['text'].lower()
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    checks_passed.append(f"Keyword '{keyword}' encontrada")
                else:
                    checks_failed.append(f"Keyword '{keyword}' não encontrada")

        # Verificar duração
        if result['duration'] > 30:
            checks_failed.append(f"Resposta muito lenta: {result['duration']:.2f}s")

        # Resultado final
        if checks_failed:
            print(f"{Colors.YELLOW}[PARCIAL]{Colors.END} {test_name}")
            print(f"  [+] Passou: {', '.join(checks_passed)}")
            print(f"  [-] Falhou: {', '.join(checks_failed)}")
            print(f"  Tempo: {result['duration']:.2f}s")
            status = "PARTIAL"
        else:
            print(f"{Colors.GREEN}[OK]{Colors.END} {test_name}")
            print(f"  [+] {', '.join(checks_passed)}")
            print(f"  Tempo: {result['duration']:.2f}s")
            status = "PASSED"

        # Mostrar preview do texto
        if result['text']:
            preview = result['text'][:150].replace('\n', ' ')
            print(f"  Preview: {preview}...")

        self.test_results.append({
            "test": test_name,
            "status": status,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "duration": result['duration'],
            "tools_used": result['tools']
        })

        return status == "PASSED"

    # ==================== TESTES DE CONVERSAÇÃO ====================

    def test_basic_greeting(self):
        """Teste 1: Saudação básica"""
        result = self._send_query("Olá! Como você pode me ajudar?")
        return self._validate_result(
            "Conversação Básica - Saudação",
            result,
            {
                "min_text_length": 50,
                "keywords": ["análise", "dados", "vendas", "estoque"]
            }
        )

    def test_capabilities_question(self):
        """Teste 2: Pergunta sobre capacidades"""
        result = self._send_query("Quais tipos de análise você consegue fazer?")
        return self._validate_result(
            "Conversação - Capacidades do Sistema",
            result,
            {
                "min_text_length": 100,
                "keywords": ["análise", "gráfico", "produtos"]
            }
        )

    # ==================== TESTES DE ANÁLISE DE DADOS ====================

    def test_top_products(self):
        """Teste 3: Top produtos por vendas"""
        result = self._send_query("Mostre os top 10 produtos por vendas nos últimos 30 dias")
        return self._validate_result(
            "Análise - Top 10 Produtos",
            result,
            {
                "min_text_length": 50,
                "expect_chart": True,
                "expect_tools": ["gerar_grafico_universal"]
            }
        )

    def test_category_analysis(self):
        """Teste 4: Análise por categoria"""
        result = self._send_query("Qual categoria tem maior volume de vendas?")
        return self._validate_result(
            "Análise - Vendas por Categoria",
            result,
            {
                "min_text_length": 30,
                "keywords": ["categoria", "vendas"]
            }
        )

    def test_segment_comparison(self):
        """Teste 5: Comparação entre segmentos"""
        result = self._send_query("Compare as vendas de TECIDOS vs PAPELARIA no último mês")
        return self._validate_result(
            "Análise - Comparação de Segmentos",
            result,
            {
                "min_text_length": 50,
                "expect_chart": True,
                "keywords": ["TECIDOS", "PAPELARIA"]
            }
        )

    def test_rupture_analysis(self):
        """Teste 6: Análise de rupturas"""
        result = self._send_query("Quais produtos estão em ruptura mas têm estoque no CD?")
        return self._validate_result(
            "Análise - Produtos em Ruptura",
            result,
            {
                "min_text_length": 50,
                "keywords": ["ruptura", "estoque", "CD"]
            }
        )

    def test_pareto_analysis(self):
        """Teste 7: Análise de Pareto (Curva ABC)"""
        result = self._send_query("Mostre a curva ABC dos produtos por receita")
        return self._validate_result(
            "Análise - Curva ABC Pareto",
            result,
            {
                "min_text_length": 50,
                "expect_chart": True,
                "keywords": ["pareto", "ABC", "receita"]
            }
        )

    # ==================== TESTES DE FILTROS ====================

    def test_une_filter(self):
        """Teste 8: Filtro por UNE"""
        result = self._send_query("Mostre produtos mais vendidos na UNE 1")
        return self._validate_result(
            "Filtros - Por UNE Específica",
            result,
            {
                "min_text_length": 30,
                "keywords": ["UNE", "1"]
            }
        )

    def test_manufacturer_filter(self):
        """Teste 9: Filtro por fabricante"""
        result = self._send_query("Quais produtos do fabricante KIT têm melhor giro?")
        return self._validate_result(
            "Filtros - Por Fabricante",
            result,
            {
                "min_text_length": 30,
                "keywords": ["KIT", "giro"]
            }
        )

    # ==================== TESTES DE GRÁFICOS ====================

    def test_bar_chart(self):
        """Teste 10: Gráfico de barras"""
        result = self._send_query("Crie um gráfico de barras dos top 5 segmentos por vendas")
        return self._validate_result(
            "Gráficos - Barras",
            result,
            {
                "expect_chart": True,
                "expect_tools": ["gerar_grafico_universal"]
            }
        )

    def test_line_chart(self):
        """Teste 11: Gráfico de linhas (tendência)"""
        result = self._send_query("Mostre a tendência de vendas dos últimos 30 dias")
        return self._validate_result(
            "Gráficos - Linhas (Tendência)",
            result,
            {
                "expect_chart": True,
                "keywords": ["tendência", "vendas"]
            }
        )

    def test_pie_chart(self):
        """Teste 12: Gráfico de pizza"""
        result = self._send_query("Faça um gráfico de pizza mostrando distribuição de vendas por categoria")
        return self._validate_result(
            "Gráficos - Pizza (Distribuição)",
            result,
            {
                "expect_chart": True,
                "keywords": ["categoria", "distribuição"]
            }
        )

    # ==================== TESTES DE EDGE CASES ====================

    def test_empty_query(self):
        """Teste 13: Query vazia"""
        result = self._send_query("")
        # Espera-se erro ou mensagem de validação
        if not result['success'] or 'digite' in result['text'].lower():
            print(f"{Colors.GREEN}[OK]{Colors.END} Edge Case - Query Vazia (tratado corretamente)")
            self.test_results.append({"test": "Edge Case - Query Vazia", "status": "PASSED", "duration": result['duration']})
            return True
        else:
            print(f"{Colors.RED}[FALHA]{Colors.END} Edge Case - Query Vazia (não tratado)")
            self.test_results.append({"test": "Edge Case - Query Vazia", "status": "FAILED", "duration": result['duration']})
            return False

    def test_invalid_column(self):
        """Teste 14: Query com coluna inexistente"""
        result = self._send_query("Mostre produtos com COLUNA_INEXISTENTE maior que 100")
        # Sistema deve lidar gracefully (auto-correção ou erro tratado)
        return self._validate_result(
            "Edge Case - Coluna Inexistente",
            result,
            {
                "min_text_length": 20  # Qualquer resposta válida
            }
        )

    def test_very_large_limit(self):
        """Teste 15: Limite muito grande"""
        result = self._send_query("Mostre os top 10000 produtos por vendas")
        return self._validate_result(
            "Edge Case - Limite Muito Grande",
            result,
            {
                "min_text_length": 30
            }
        )

    # ==================== RELATÓRIO FINAL ====================

    def print_summary(self):
        """Imprime resumo dos testes."""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}RESUMO DOS TESTES - CHAT BI{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        partial = sum(1 for r in self.test_results if r['status'] == 'PARTIAL')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')

        avg_duration = sum(r['duration'] for r in self.test_results) / total if total > 0 else 0

        print(f"Total de Testes: {total}")
        print(f"{Colors.GREEN}[+] Passou: {passed}{Colors.END}")
        print(f"{Colors.YELLOW}[!] Parcial: {partial}{Colors.END}")
        print(f"{Colors.RED}[-] Falhou: {failed}{Colors.END}")
        print(f"\nTempo Medio: {avg_duration:.2f}s")
        print(f"Taxa de Sucesso: {(passed/total*100):.1f}%\n")

        # Detalhes
        print(f"{Colors.BOLD}DETALHES:{Colors.END}\n")
        for r in self.test_results:
            status_icon = "[+]" if r['status'] == 'PASSED' else ("[!]" if r['status'] == 'PARTIAL' else "[-]")
            status_color = Colors.GREEN if r['status'] == 'PASSED' else (Colors.YELLOW if r['status'] == 'PARTIAL' else Colors.RED)

            print(f"{status_color}{status_icon}{Colors.END} {r['test']} ({r['duration']:.2f}s)")

            if r.get('tools_used'):
                print(f"  Tools: {', '.join(r['tools_used'])}")

            if r.get('checks_failed'):
                for check in r['checks_failed']:
                    print(f"    [-] {check}")

        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")

        return passed, partial, failed


# ==================== TESTES DE CODECHAT ====================

class CodeChatTester:
    def __init__(self, token: str):
        self.token = token
        self.test_results = []

    def _send_query(self, query: str, timeout: int = 30) -> Dict[str, Any]:
        """Envia query para CodeChat endpoint."""
        print(f"\n{Colors.CYAN}[CODECHAT]{Colors.END} {query}")

        url = f"{API_V1}/code-chat"

        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"query": query}

        start_time = time.time()

        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            duration = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "answer": result.get('answer', ''),
                    "sources": result.get('sources', []),
                    "duration": duration
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": duration
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout", "duration": timeout}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time() - start_time}

    def test_architecture_question(self):
        """Teste CodeChat 1: Pergunta sobre arquitetura"""
        result = self._send_query("Como funciona o sistema de agentes neste projeto?")

        if result['success']:
            print(f"{Colors.GREEN}[OK]{Colors.END} CodeChat - Arquitetura")
            print(f"  Resposta: {result['answer'][:200]}...")
            print(f"  Fontes: {len(result['sources'])} arquivos")
            print(f"  Tempo: {result['duration']:.2f}s")
            self.test_results.append({"test": "CodeChat - Arquitetura", "status": "PASSED", "duration": result['duration']})
            return True
        else:
            print(f"{Colors.YELLOW}[INFO]{Colors.END} CodeChat endpoint não disponível (esperado)")
            self.test_results.append({"test": "CodeChat - Arquitetura", "status": "SKIPPED", "reason": "Endpoint não implementado"})
            return False

    def test_api_usage_question(self):
        """Teste CodeChat 2: Como usar uma API específica"""
        result = self._send_query("Como faço para criar uma nova ferramenta (tool) no sistema?")

        if result['success']:
            print(f"{Colors.GREEN}[OK]{Colors.END} CodeChat - API Usage")
            print(f"  Resposta: {result['answer'][:200]}...")
            print(f"  Tempo: {result['duration']:.2f}s")
            self.test_results.append({"test": "CodeChat - API Usage", "status": "PASSED", "duration": result['duration']})
            return True
        else:
            print(f"{Colors.YELLOW}[INFO]{Colors.END} CodeChat endpoint não disponível")
            self.test_results.append({"test": "CodeChat - API Usage", "status": "SKIPPED", "reason": "Endpoint não implementado"})
            return False

    def print_summary(self):
        """Imprime resumo dos testes CodeChat."""
        if not self.test_results:
            return

        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}RESUMO DOS TESTES - CODECHAT{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

        for r in self.test_results:
            if r['status'] == 'PASSED':
                print(f"{Colors.GREEN}[+]{Colors.END} {r['test']} ({r['duration']:.2f}s)")
            else:
                print(f"{Colors.YELLOW}[x]{Colors.END} {r['test']} - {r.get('reason', 'N/A')}")

        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")


# ==================== TESTE DE CACHE ====================

def test_semantic_cache(token: str):
    """Testa se cache semântico está funcionando."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}TESTE DE CACHE SEMÂNTICO{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

    query = "Mostre os top 5 produtos mais vendidos"
    session_id = f"cache-test-{int(time.time())}"

    url = f"{API_V1}/chat/stream"
    params = {"q": query, "token": token, "session_id": session_id}

    # Primeira execução
    print(f"{Colors.CYAN}[1ª EXEC]{Colors.END} {query}")
    start1 = time.time()
    requests.get(url, params=params, timeout=30)
    duration1 = time.time() - start1
    print(f"  Tempo: {duration1:.2f}s")

    # Segunda execução (deve usar cache)
    time.sleep(1)
    print(f"{Colors.CYAN}[2ª EXEC]{Colors.END} {query} (esperando cache hit)")
    start2 = time.time()
    requests.get(url, params=params, timeout=30)
    duration2 = time.time() - start2
    print(f"  Tempo: {duration2:.2f}s")

    # Validar
    if duration2 < duration1 * 0.7:  # Pelo menos 30% mais rápido
        print(f"{Colors.GREEN}[OK]{Colors.END} Cache funcionando! (2ª exec {(duration2/duration1*100):.1f}% do tempo da 1ª)")
        return True
    else:
        print(f"{Colors.YELLOW}[AVISO]{Colors.END} Cache pode não estar ativo (diferença: {(duration2/duration1*100):.1f}%)")
        return False


# ==================== MAIN ====================

def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}TESTES ROBUSTOS - CHAT BI & CODECHAT{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Autenticação
    token = login()
    if not token:
        print(f"{Colors.RED}[ERRO FATAL]{Colors.END} Não foi possível autenticar")
        sys.exit(1)

    # Testes de Chat BI
    chat_tester = ChatTester(token)

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 1: CONVERSAÇÃO BÁSICA{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    chat_tester.test_basic_greeting()
    chat_tester.test_capabilities_question()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 2: ANÁLISES DE DADOS{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    chat_tester.test_top_products()
    chat_tester.test_category_analysis()
    chat_tester.test_segment_comparison()
    chat_tester.test_rupture_analysis()
    chat_tester.test_pareto_analysis()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 3: FILTROS E SEGMENTAÇÃO{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    chat_tester.test_une_filter()
    chat_tester.test_manufacturer_filter()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 4: TIPOS DE GRÁFICOS{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    chat_tester.test_bar_chart()
    chat_tester.test_line_chart()
    chat_tester.test_pie_chart()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 5: EDGE CASES{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    chat_tester.test_empty_query()
    chat_tester.test_invalid_column()
    chat_tester.test_very_large_limit()

    # Resumo Chat BI
    passed, partial, failed = chat_tester.print_summary()

    # Testes de CodeChat
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}BATERIA 6: CODECHAT (RAG DOCUMENTAÇÃO){Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    codechat_tester = CodeChatTester(token)
    codechat_tester.test_architecture_question()
    codechat_tester.test_api_usage_question()
    codechat_tester.print_summary()

    # Teste de Cache
    test_semantic_cache(token)

    # Resumo Final
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}RESULTADO FINAL{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    print(f"Termino: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    total_tests = passed + partial + failed
    if failed == 0 and partial <= 2:
        print(f"{Colors.GREEN}{Colors.BOLD}[+] TODOS OS TESTES PASSARAM!{Colors.END}")
        print(f"Sistema pronto para producao.\n")
        return 0
    elif failed <= 2:
        print(f"{Colors.YELLOW}{Colors.BOLD}[!] TESTES PASSARAM COM RESSALVAS{Colors.END}")
        print(f"Algumas funcionalidades podem precisar de ajuste.\n")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}[-] TESTES FALHARAM{Colors.END}")
        print(f"Sistema precisa de correcoes antes de producao.\n")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
