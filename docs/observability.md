# Arquitetura de Observabilidade Cognitiva - Caculinha BI

## 1. Objetivos e Escopo
Implementar uma stack de observabilidade de ponta a ponta ("Glass Box") para a plataforma Caculinha BI, focada em três pilares:
1.  **Rastreabilidade Técnica:** Logs estruturados e Tracing distribuído (OpenTelemetry).
2.  **Rastreabilidade de Negócio:** Contexto Multi-tenant (`tenant_id`) e Métricas de Uso.
3.  **Rastreabilidade Cognitiva:** "Agent Trace" para visualizar o raciocínio e execução dos agentes de IA.

**Escopo:** Backend (FastAPI), Agentes (LangChain/LangGraph), Banco de Dados (DuckDB/SQL) e Integrações LLM.

---

## 2. Schema de Logs (JSON Estruturado)

Todos os logs da aplicação devem ser emitidos em JSON (stdout) seguindo este schema padrão.

### Campos Padrão
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `timestamp` | ISO8601 | Sim | Momento do evento (UTC) |
| `level` | String | Sim | INFO, WARN, ERROR, DEBUG |
| `message` | String | Sim | Mensagem legível para humanos |
| `service` | String | Sim | `caculinha-bi` |
| `request_id` | UUID | Não | ID único da requisição HTTP (correlação) |
| `tenant_id` | String | Não | ID do cliente/loja contextuado |
| `trace_id` | Hex | Não | OpenTelemetry Trace ID |
| `span_id` | Hex | Não | OpenTelemetry Span ID |
| `component` | String | Não | Módulo origem (ex: `auth`, `agent.orchestrator`) |

### Exemplo de Log
```json
{
  "timestamp": "2026-02-07T18:30:00.123Z",
  "level": "INFO",
  "service": "caculinha-bi",
  "message": "Tool execution completed",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "tenant_id": "loja-1685",
  "component": "agent.backend_specialist",
  "extra": {
    "tool": "consultar_faturamento",
    "duration_ms": 450
  }
}
```

---

## 3. Estratégia de Correlação

A correlação entre logs, métricas e traces é garantida por 3 identificadores propagados em **Context Vars**:

1.  **Request ID (`X-Request-Id`):**
    - Gerado no Middleware (ou recebido do Load Balancer).
    - Propagado em todos os logs e chamadas downstream.
    - Retornado ao cliente no header de resposta.

2.  **Tenant ID (`X-Tenant-Id`):**
    - Resolvido via JWT ou Header.
    - Obrigatório para segregação de dados e métricas.

3.  **Trace ID (OpenTelemetry):**
    - W3C Trace Context (`traceparent`).
    - Vincula logs aos spans de tracing.

---

## 4. Agent Trace (Rastreabilidade Cognitiva)

Um coletor específico para capturar o "pensamento" dos agentes.

### Estrutura de Dados
```json
{
  "trace_id": "550e8400-e29b...",
  "request_id": "123e4567...",
  "tenant_id": "loja-123",
  "agent": "Orchestrator",
  "start_time": "2026-02-07T18:30:00Z",
  "end_time": "2026-02-07T18:30:05Z",
  "status": "success",
  "steps": [
    {
      "step_id": 1,
      "type": "thought",
      "content": "Preciso consultar o faturamento..."
    },
    {
      "step_id": 2,
      "type": "tool_call",
      "tool": "consultar_vendas",
      "input": {"loja": "1685"},
      "duration_ms": 300
    },
    {
      "step_id": 3,
      "type": "llm_call",
      "model": "gemini-2.5-flash",
      "tokens_in": 150,
      "tokens_out": 50,
      "cost_usd": 0.00012
    }
  ],
  "total_tokens": 200,
  "total_cost": 0.00012
}
```

---

## 5. Métricas Prometheus (Monitoramento)

Expostas em `/metrics`.

### Golden Signals (HTTP)
- `caculinha_http_requests_total{route, method, status, tenant}`
- `caculinha_http_request_duration_seconds{route, method, tenant}` (Histograma)

### Métricas de IA/Agentes
- `caculinha_agent_invocations_total{agent, tenant, status}`
- `caculinha_agent_duration_seconds{agent, tenant}` (Histograma)
- `caculinha_llm_tokens_total{model, direction, tenant}` (Counter)
- `caculinha_llm_cost_estimated_total{model, tenant}` (Counter)
- `caculinha_rag_retrievals_total{tenant, source}` (Counter)
- `caculinha_tool_execution_total{tool, status, tenant}`

### Métricas de Erro
- `caculinha_errors_total{component, type, tenant}`

---

## 6. Estratégia de Redaction (Segurança)

NENHUM dado sensível deve ser logado.

**Regras de Redaction:**
1.  **Headers:** `Authorization`, `X-API-Key` → Substituir por `[REDACTED]`.
2.  **Corpo JSON:** Campos como `password`, `token`, `secret`, `cpf` → Mascarar valor.
3.  **Agent Trace:** Não persistir o prompt bruto se contiver PII (analisar caso a caso).

---

## 7. Infraestrutura Local

Ambiente de desenvolvimento com Docker Compose:

- **App:** Porta 8000
- **Prometheus:** Porta 9090 (Scrape config apontando para `app:8000/metrics`)
- **OpenTelemetry Collector (Opcional):** Porta 4317/4318

### Como Rodar
```bash
docker-compose up -d
```

---

## ✅ Checklist de Aceite da Fase 1

- [x] Arquivo `docs/observability.md` criado e detalhado.
- [x] Schema de logs definido (JSON).
- [x] Estratégia de correlação definida (Request/Tenant/Trace).
- [x] Métricas Prometheus especificadas.
- [x] Formato do Agent Trace definido.
