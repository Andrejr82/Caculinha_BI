# Baseline de Testes - Caculinha BI Enterprise Platform

**Data:** 2026-02-07
**Status:** FASE 0 CONCLUÍDA

## 1. Ambiente de Teste
- **Python:** 3.11+
- **Pytest:** 9.0.1
- **Sistema Operacional:** Windows

## 2. Plugins Ativos
- `pytest-asyncio` (1.3.0): Suporte a loops assíncronos
- `pytest-cov` (7.0.0): Relatório de cobertura
- `pytest-timeout` (2.4.0): Limite de tempo para testes travados

## 3. Estrutura de Testes
- **Raiz de Testes:** `backend/tests`
- **Configuração:** `pytest.ini` (Raiz do Projeto)
- **Bootstrap:** `backend/tests/conftest.py` (Injeção de `sys.path`)
- **Padrão de Importação:** `from app...` (Habilitado via injeção de `backend/` no path)

## 4. Comandos Oficiais
- **Executar Tudo (Smoke):** `python -m pytest`
- **Executar Unidade:** `python -m pytest backend/tests/unit`
- **Executar Integração:** `python -m pytest backend/tests/integration`

## 5. Riscos e Exclusões Conhecidas
Os seguintes arquivos estão **ignorados** no `pytest.ini` devido a erros de dependência ou legado:
1. `backend/tests/e2e/test_chat_flow.py` (Requer Playwright)
2. `backend/tests/load/test_30_users.py` (Requer Locust)
3. `backend/tests/test_final_corrected.py` (Erro de arquivo)
4. `backend/tests/test_final_sse.py` (Erro de arquivo)
5. `backend/tests/test_tool_config.py` (Erro de arquivo)
6. `backend/tests/test_tool_selection.py` (Erro de arquivo)
7. `backend/tests/test_gemini_integration.py` (Import inválido)
8. `backend/tests/test_integration_dados_reais.py` (NameError)
9. `backend/tests/test_security_resilience.py` (Compatibilidade Pydantic)
10. `backend/tests/test_tool_modernization.py` (API Pytest antiga)
11. `backend/tests/unit/test_caculinha_bi_agent.py` (Import inválido)
12. `backend/tests/unit/test_code_gen_agent.py` (Import inválido)
13. `backend/tests/unit/test_une_tools.py` (Import inválido)

**Risco Crítico:** A execução da suíte completa em paralelo ou verbosa no Windows pode gerar `ValueError: I/O operation on closed file` devido a conflitos de captura de log. Recomenda-se execução segmentada.
