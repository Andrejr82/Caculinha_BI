# Documentação de Métricas Prometheus

Abaixo estão listadas as métricas expostas no endpoint `/api/v1/metrics`.

## 1. Golden Signals (Tráfego HTTP)

Métricas essenciais para monitorar saúde da API.

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_http_requests_total` | Counter | `method`, `route`, `status`, `tenant` | Total de requisições recebidas. |
| `caculinha_http_request_duration_seconds` | Histogram | `method`, `route`, `tenant` | Distribuição da latência das requisições. |

## 2. Métricas de IA e Agentes

Monitoramento específico da execução dos agentes e consumo de LLM.

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_agent_invocations_total` | Counter | `agent`, `status`, `tenant` | Total de execuções de agentes (sucesso/falha). |
| `caculinha_agent_duration_seconds` | Histogram | `agent`, `tenant` | Tempo de execução end-to-end do agente. |
| `caculinha_tool_execution_total` | Counter | `tool`, `status`, `tenant` | Uso de ferramentas específicas (ex: SQL, Chart). |
| `caculinha_rag_retrievals_total` | Counter | `source`, `tenant` | Documentos recuperados do vetor store. |

## 3. Custos e Tokens (FinOps)

Controle de gastos com APIs de LLM.

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_llm_tokens_total` | Counter | `model`, `direction`, `tenant` | Tokens de entrada e saída. |
| `caculinha_llm_cost_estimated_total` | Counter | `model`, `tenant` | Custo estimado em USD (baseado em tabela fixa). |

## 4. Erros e Exceções

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_errors_total` | Counter | `component`, `type`, `tenant` | Contagem de exceções não tratadas por componente. |
