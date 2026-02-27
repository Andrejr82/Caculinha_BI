# ChatBI Precision Playbook

## 1. Objetivo
Padronizar como o ChatBI aumenta precisão de resposta, reduz erro de roteamento e evita respostas vagas de "sem dados" sem diagnóstico.

## 2. Escopo
- Fluxo principal de chat: `backend/app/api/v1/endpoints/chat.py`
- Serviço de orquestração: `backend/app/services/chat_service_v3.py`
- Agente e governança de tools: `backend/app/core/agents/caculinha_bi_agent.py`
- Classificação e roteamento: `backend/app/core/utils/intent_classifier.py`, `backend/app/core/utils/query_router.py`
- Ferramenta de gráfico: `backend/app/core/tools/universal_chart_generator.py`

## 3. Arquitetura de precisão
1. Classificação de intenção (regex + score).
2. Seleção de ferramenta por roteador.
3. Enriquecimento de parâmetros de negócio (segmento, todas as lojas, etc.).
4. Caminho governado para execução determinística de alta confiança.
5. Formatação de resposta orientada a decisão.
6. Sanitização de saída técnica para narrativa legível.

## 4. Controles já implementados
- Reforço de intent para pedidos de gráfico com typo comum.
- Diagnóstico estruturado para `NO_DATA` com sinalização de provável bloqueio por RLS.
- Mensagem governada separando:
  - "sem dados no recorte" vs
  - "sem acesso ao segmento (RLS)".
- Sanitização neutra de resposta (`response_sanitizer`), com alias legado para compatibilidade.

## 5. Política de erro e fallback
- `NO_DATA`: dados não encontrados no recorte.
- `NO_DATA + likely_rls_block=true`: provável ausência por escopo de permissão.
- Falha técnica de tool: retornar mensagem de operação e orientar próximo ajuste de filtro.

## 6. KPIs operacionais
- `tool_selection_accuracy`: % de vezes que a tool final é a esperada para o caso.
- `chart_success_rate`: % de pedidos de gráfico com `chart_data` retornado.
- `no_data_false_positive_rate`: % de `NO_DATA` em casos com dado disponível fora do recorte atual.
- `rls_diagnostic_coverage`: % de `NO_DATA` com diagnóstico de RLS preenchido.

## 7. Critérios de aceite
- Suite crítica de regressão verde.
- Casos reais com typo roteando para visualização.
- Para `NO_DATA`, mensagem com causa operacional acionável.

## 8. Rotina semanal
1. Revisar top 20 consultas com `NO_DATA`.
2. Ajustar padrões de intent/roteamento com base em evidência.
3. Reexecutar regressão.
4. Publicar delta de métricas.

## 9. Rollback rápido
1. Reverter regras de intent/roteamento do último deploy.
2. Manter resposta segura e conservadora de tool.
3. Reexecutar suite crítica antes de novo rollout.

