# ChatBI Test Cases (Regressão de Precisão)

## 1. Objetivo
Padronizar cenários críticos que devem permanecer estáveis a cada alteração de prompt, roteamento e ferramentas.

## 2. Casos prioritários

| ID | Cenário | Query | Esperado |
|---|---|---|---|
| TC-01 | Gráfico com typo e escopo total | `me de um grafico de vendas do segmento artes de toas as unes` | Intent `visualization`, tool `gerar_grafico_universal_v2`, `filtro_segmento=ARTES` |
| TC-02 | Ranking por UNE explícita | `gere um gráfico de ranking de vendas dos segmentos na une 520` | Tool de gráfico, filtro de UNE aplicado |
| TC-03 | Sem dados por RLS | mesmo TC-01 com usuário restrito sem ARTES | `error_code=NO_DATA` e diagnóstico `likely_rls_block=true` |
| TC-04 | Sem dados por recorte | query com filtro inexistente | mensagem acionável sem falso positivo de permissão |
| TC-05 | Roteamento ruptura | `quais grupos estão com maior porcentagem de rupturas?` | tool `encontrar_rupturas_criticas` |
| TC-06 | Consulta flexível robusta | filtros/colunas em dict/json-string/csv | parsing sem crash e resposta consistente |

## 3. Suites automatizadas
- `backend/tests/test_universal_tool_selection.py`
- `backend/tests/test_chatbi_tool_routing_integration.py`
- `backend/tests/test_tool_modernization.py`
- `backend/tests/test_response_sanitizer.py`
- `backend/tests/test_chart_no_data_diagnostics.py`
- `backend/tests/test_consultar_dados_flexivel_inputs.py`

## 4. Comando de regressão recomendado
```powershell
python -m pytest `
  backend/tests/test_universal_tool_selection.py `
  backend/tests/test_chatbi_tool_routing_integration.py `
  backend/tests/test_tool_modernization.py `
  backend/tests/test_response_sanitizer.py `
  backend/tests/test_chart_no_data_diagnostics.py `
  backend/tests/test_consultar_dados_flexivel_inputs.py -q
```

## 5. Critério de aprovação
- 100% verde nas suites críticas.
- Testes manuais opcionais (dependentes de token/ambiente externo) podem ficar `skipped`.

## 6. Teste manual opcional
- `backend/tests/test_tool_config.py`  
Depende de `tests/test_token.txt` e backend ativo; sem isso, o teste deve ser `skipped`.

