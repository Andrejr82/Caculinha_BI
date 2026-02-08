# Dashboard de Observabilidade (Mock)

Este documento exemplifica como visualizar os dados coletados no Grafana.

## 1. Overview da Plataforma

**Painel Superior: Saúde do Sistema**

| Métrica | Visualização | Query PromQL |
|---------|--------------|--------------|
| **Total Requests** | Stat (Big Number) | `sum(rate(caculinha_http_requests_total[5m]))` |
| **Error Rate** | Gauge (0-100%) | `sum(rate(caculinha_http_requests_total{status=~"5.."}[5m])) / sum(rate(caculinha_http_requests_total[5m]))` |
| **Latency (p95)** | Time Series | `histogram_quantile(0.95, sum(rate(caculinha_http_request_duration_seconds_bucket[5m]) by (le)))` |

---

## 2. Monitoramento de Agentes (AI Insights)

**Painel Central: Performance dos Agentes**

| Métrica | Visualização | Query PromQL |
|---------|--------------|--------------|
| **Agentes Ativos** | Bar Chart | `sum(rate(caculinha_agent_invocations_total[1h])) by (agent)` |
| **Custo LLM ($)** | Stat (Currency) | `sum(increase(caculinha_llm_cost_estimated_total[24h]))` |
| **Tokens / Minuto** | Time Series | `sum(rate(caculinha_llm_tokens_total[5m])) by (model)` |

---

## 3. Logs de Rastreabilidade (Loki / Discover)

Exemplo de visualização de logs correlacionados pelo `trace_id`.

**Filtro:** `trace_id = "a1b2c3d4..."`

```log
[INFO] http_request_started method=POST path=/api/v2/chat
[INFO] Agent Orchestrator initialized input="analisar vendas"
[INFO] Tool Execution: sql_query duration=1.2s
[INFO] LLM Generation model=gemini-1.5-pro tokens=150
[INFO] http_request_finished status=200 duration=2.5s
```
