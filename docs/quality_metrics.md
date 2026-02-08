# Métricas de Qualidade e Governança (Prometheus)

Este documento descreve as métricas expostas pelo Response Quality Gate.

## 1. Golden Signals de Qualidade

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_response_quality_score` | Gauge | `tenant`, `agent` | Nota de fluidez e tom da resposta (0-1). |
| `caculinha_response_utility_score` | Gauge | `tenant`, `agent` | Nota de utilidade para decisão de negócio (0-1). |
| `caculinha_response_groundedness_score` | Gauge | `tenant`, `agent` | Fidelidade aos dados retornados pelo RAG (0-1). |

## 2. Métricas de Operação

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `caculinha_responses_blocked_total` | Counter | `tenant` | Total de respostas que falharam no gate (<0.5). |
| `caculinha_responses_warning_total` | Counter | `tenant` | Total de respostas com confiança moderada (0.5-0.8). |

## 3. Visualização Recomendada (Grafana)

### Dashboard de Governança:
- **Painel de Alucinação:** Gráfico de linha de `groundedness_score`. Quedas bruscas indicam problemas no RAG ou no LLM.
- **Taxa de Bloqueio:** `rate(caculinha_responses_blocked_total[5m])`. Picos indicam que o agente está gerando respostas perigosas.
- **Saúde por Tenant:** Comparativo de `utility_score` entre diferentes empresas/lojas.

## 4. Logs Relacionados

As métricas são complementadas pelos logs JSON:
```json
{
  "event": "response_blocked_by_quality_gate",
  "scores": {"quality": 0.4, "utility": 0.6, "groundedness": 0.3},
  "request_id": "...",
  "conversation_id": "..."
}
```
