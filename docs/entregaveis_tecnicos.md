# Entregáveis Técnicos Q2 2026

**Projeto:** Caculinha BI Enterprise AI Platform  
**Período:** Abril — Junho 2026

---

## Iniciativa 1: Observabilidade Completa

### Arquitetura Afetada
- **Camada:** Infrastructure
- **Componentes:** Logging, Metrics, Tracing

### Agentes Envolvidos
- Backend Specialist (implementação)
- Security Auditor (revisão de logs sensíveis)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Port | `IMetricsPort` | **NOVO** |
| Port | `ITracingPort` | **NOVO** |
| Adapter | `OpenTelemetryAdapter` | **NOVO** |
| Adapter | `PrometheusAdapter` | **NOVO** |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/metrics` | GET | Métricas Prometheus |
| `/health` | GET | Health check detalhado |
| `/ready` | GET | Readiness probe |

### Testes Esperados

- [ ] Teste de coleta de métricas
- [ ] Teste de propagação de trace
- [ ] Teste de health check
- [ ] Teste de integração com Grafana

---

## Iniciativa 2: Billing SaaS

### Arquitetura Afetada
- **Camada:** Application + Infrastructure
- **Componentes:** Payments, Subscriptions, Quotas

### Agentes Envolvidos
- Backend Specialist (API Stripe)
- Security Auditor (PCI compliance)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Port | `IPaymentPort` | **NOVO** |
| Port | `ISubscriptionPort` | **NOVO** |
| Adapter | `StripePaymentAdapter` | **NOVO** |
| Entity | `Subscription` | **NOVO** |
| Entity | `Invoice` | **NOVO** |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/billing/subscribe` | POST | Criar assinatura |
| `/billing/plans` | GET | Listar planos |
| `/billing/usage` | GET | Consumo atual |
| `/billing/invoices` | GET | Histórico de faturas |
| `/webhooks/stripe` | POST | Webhook Stripe |

### Testes Esperados

- [ ] Teste de criação de assinatura
- [ ] Teste de upgrade/downgrade
- [ ] Teste de cancelamento
- [ ] Teste de webhook (mock)
- [ ] Teste de quota enforcement

---

## Iniciativa 3: Multi-Tenancy Hardening

### Arquitetura Afetada
- **Camada:** Core (Security)
- **Componentes:** TenantResolver, RBAC, Row-Level Security

### Agentes Envolvidos
- Security Auditor (design)
- Backend Specialist (implementação)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Adapter | `TenantResolver` | **MODIFICAR** |
| Adapter | `SQLiteMemoryAdapter` | **MODIFICAR** (RLS) |
| Adapter | `DuckDBVectorAdapter` | **MODIFICAR** (RLS) |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/admin/tenants` | GET | Listar tenants |
| `/admin/tenants/{id}` | PUT | Atualizar tenant |
| `/admin/tenants/{id}/usage` | GET | Uso por tenant |

### Testes Esperados

- [ ] Teste de isolamento de dados
- [ ] Teste de cross-tenant access (deve falhar)
- [ ] Teste de RLS em queries
- [ ] Pentest de isolamento

---

## Iniciativa 4: Dashboard Analytics

### Arquitetura Afetada
- **Camada:** Frontend
- **Componentes:** Charts, Widgets, Layout

### Agentes Envolvidos
- Frontend Specialist (UI)
- Backend Specialist (APIs de dados)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| API | `/analytics/*` | **NOVO** |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/analytics/sales/summary` | GET | Resumo de vendas |
| `/analytics/sales/trend` | GET | Tendência temporal |
| `/analytics/inventory/status` | GET | Status de estoque |
| `/analytics/ruptures/top` | GET | Top rupturas |
| `/analytics/widgets/config` | GET/PUT | Config de widgets |

### Testes Esperados

- [ ] Teste de componentes Chart (Vitest)
- [ ] Teste E2E de dashboard (Playwright)
- [ ] Teste de responsividade
- [ ] Teste de performance (Lighthouse)

---

## Iniciativa 5: Chat UX Premium

### Arquitetura Afetada
- **Camada:** Frontend + API
- **Componentes:** ChatStream, Markdown, CodeBlock

### Agentes Envolvidos
- Frontend Specialist (UI)
- Backend Specialist (SSE)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Endpoint | `/chat/stream` | **NOVO** (SSE) |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/chat/stream` | POST (SSE) | Chat com streaming |

### Testes Esperados

- [ ] Teste de SSE connection
- [ ] Teste de markdown rendering
- [ ] Teste de code syntax highlight
- [ ] Teste de latência < 200ms

---

## Iniciativa 6: Auto-Training Pipeline

### Arquitetura Afetada
- **Camada:** Application (Agents) + Infrastructure
- **Componentes:** FeatureStore, Training, Feedback

### Agentes Envolvidos
- Backend Specialist (pipeline)
- Orchestrator (coordenação)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Agent | `TrainingAgent` | **NOVO** |
| Port | `ITrainingPort` | **NOVO** |
| Adapter | `FeedbackCollector` | **NOVO** |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/training/trigger` | POST | Disparar training |
| `/training/status` | GET | Status do job |
| `/training/history` | GET | Histórico de runs |

### Testes Esperados

- [ ] Teste de coleta de feedback
- [ ] Teste de agregação de features
- [ ] Teste de pipeline execution
- [ ] Teste de rollback de modelo

---

## Iniciativa 7: Anomaly Detection

### Arquitetura Afetada
- **Camada:** Application (Agents)
- **Componentes:** Analytics, Alerts

### Agentes Envolvidos
- Backend Specialist (algoritmos)
- Insight Agent (narrativa)

### Ports/Adapters Afetados

| Tipo | Nome | Ação |
|------|------|------|
| Agent | `AnomalyAgent` | **NOVO** |
| Port | `IAnomalyDetector` | **NOVO** |

### APIs Novas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/anomalies/detect` | POST | Detectar anomalias |
| `/anomalies/alerts` | GET | Alertas ativos |
| `/anomalies/config` | PUT | Configurar thresholds |

### Testes Esperados

- [ ] Teste de detecção Z-score
- [ ] Teste de alertas
- [ ] Teste de false positives
- [ ] Teste de performance em volume

---

## Resumo de Entregáveis

| Iniciativa | Novos Ports | Novos Adapters | Novas APIs | Testes |
|------------|-------------|----------------|------------|--------|
| Observabilidade | 2 | 2 | 3 | 4 |
| Billing | 2 | 1 | 5 | 5 |
| Multi-Tenancy | 0 | 0 (mod) | 3 | 4 |
| Dashboard | 0 | 0 | 5 | 4 |
| Chat UX | 0 | 0 | 1 | 4 |
| Auto-Training | 1 | 1 | 3 | 4 |
| Anomaly | 1 | 0 | 3 | 4 |
| **TOTAL** | **6** | **4** | **23** | **29** |

---

**Próxima Revisão:** 01/04/2026
