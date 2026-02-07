# Arquitetura — Caculinha BI Agent Platform

**Data:** 2026-02-07  
**Versão:** 2.0.0  
**Autor:** Arquiteto de Sistema

---

## 1. Visão Arquitetural

O sistema segue **Clean Architecture** com separação clara entre camadas:

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                     │
│                    (API REST + Middlewares)                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     APPLICATION LAYER                       │
│                   (Agents + Use Cases)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                       DOMAIN LAYER                          │
│                (Entities + Value Objects + Ports)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   INFRASTRUCTURE LAYER                      │
│                      (Adapters)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Estrutura de Diretórios

```
backend/
├── domain/                     # CAMADA DE DOMÍNIO
│   ├── entities/               # Entidades de negócio
│   │   ├── agent.py            # Entidade Agent
│   │   ├── conversation.py     # Entidade Conversation
│   │   ├── insight.py          # Entidade Insight
│   │   ├── forecast.py         # Entidade Forecast
│   │   └── tenant.py           # Entidade Tenant
│   │
│   ├── value_objects/          # Value Objects
│   │   ├── tenant_id.py        # VO TenantId
│   │   ├── user_id.py          # VO UserId
│   │   ├── message_id.py       # VO MessageId
│   │   └── time_range.py       # VO TimeRange
│   │
│   └── ports/                  # Contratos (Interfaces)
│       ├── llm_port.py         # Interface LLM
│       ├── data_source_port.py # Interface Data Source
│       ├── cache_port.py       # Interface Cache
│       ├── auth_port.py        # Interface Auth
│       ├── metrics_port.py     # Interface Metrics
│       └── agent_port.py       # Interface Agent
│
├── application/                # CAMADA DE APLICAÇÃO
│   └── agents/                 # Agentes especializados
│       ├── base_agent.py       # Classe base
│       ├── orchestrator_agent.py
│       ├── sql_agent.py
│       ├── insight_agent.py
│       ├── forecast_agent.py
│       ├── metadata_agent.py
│       ├── tenant_agent.py
│       ├── security_agent.py
│       └── monitoring_agent.py
│
├── infrastructure/             # CAMADA DE INFRAESTRUTURA
│   └── adapters/
│       ├── llm/
│       │   └── gemini_adapter.py    # Implementação LLMPort
│       └── data/
│           └── duckdb_adapter.py     # Implementação DataSourcePort
│
├── api/                        # CAMADA DE APRESENTAÇÃO
│   ├── middleware/             # Middlewares
│   │   ├── auth.py             # AuthMiddleware (JWT)
│   │   ├── tenant.py           # TenantMiddleware
│   │   └── rate_limit.py       # RateLimitMiddleware
│   │
│   └── v2/endpoints/           # Endpoints REST
│       ├── health.py           # /health
│       ├── auth.py             # /auth
│       ├── chat.py             # /chat
│       ├── agents.py           # /agents
│       └── metrics.py          # /metrics
│
├── services/                   # Serviços de infraestrutura
│   ├── metrics.py              # MetricsService
│   ├── billing.py              # BillingService
│   └── logging_config.py       # Logging estruturado
│
└── main.py                     # Entry point FastAPI
```

---

## 3. Fluxo de Dados

```
┌───────────┐     ┌────────────┐     ┌────────────────┐
│  Cliente  │────▶│   API v2   │────▶│  Orchestrator  │
│  (HTTP)   │     │ (FastAPI)  │     │    Agent       │
└───────────┘     └────────────┘     └───────┬────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
       ┌──────▼──────┐              ┌────────▼────────┐            ┌───────▼───────┐
       │  SQLAgent   │              │  InsightAgent   │            │ ForecastAgent │
       └──────┬──────┘              └────────┬────────┘            └───────┬───────┘
              │                              │                              │
       ┌──────▼──────┐              ┌────────▼────────┐            ┌───────▼───────┐
       │   DuckDB    │              │     Gemini      │            │    Gemini     │
       │  Adapter    │              │    Adapter      │            │   Adapter     │
       └──────┬──────┘              └────────┬────────┘            └───────┬───────┘
              │                              │                              │
       ┌──────▼──────┐              ┌────────▼────────┐            ┌───────▼───────┐
       │  Parquet    │              │   Google LLM    │            │  Google LLM   │
       │   Files     │              │   (gemini-2.5)  │            │  (gemini-2.5) │
       └─────────────┘              └─────────────────┘            └───────────────┘
```

---

## 4. Componentes Principais

### 4.1 Agentes (8 especializados)

| Agente | Responsabilidade |
|--------|------------------|
| **OrchestratorAgent** | Roteamento e coordenação |
| **SQLAgent** | Queries SQL via DuckDB |
| **InsightAgent** | Narrativas e análises |
| **ForecastAgent** | Previsões e tendências |
| **MetadataAgent** | Schema e dicionário de dados |
| **TenantAgent** | Multi-tenancy |
| **SecurityAgent** | Auditoria e validação |
| **MonitoringAgent** | Saúde do sistema |

### 4.2 Ports (Interfaces)

| Port | Propósito |
|------|-----------|
| **LLMPort** | Abstração de LLMs (Gemini, Groq) |
| **DataSourcePort** | Abstração de fontes de dados |
| **CachePort** | Abstração de cache |
| **AuthPort** | Abstração de autenticação |
| **MetricsPort** | Abstração de métricas |
| **AgentPort** | Contrato base de agentes |

### 4.3 Adapters (Implementações)

| Adapter | Port Implementado |
|---------|-------------------|
| **GeminiAdapter** | LLMPort |
| **DuckDBAdapter** | DataSourcePort |
| **AuthMiddleware** | AuthPort |
| **MetricsService** | MetricsPort |

---

## 5. Tecnologias

| Camada | Tecnologia |
|--------|------------|
| **Runtime** | Python 3.11+ |
| **Framework** | FastAPI |
| **LLM** | Google Gemini 2.5 |
| **Data Engine** | DuckDB + Parquet |
| **Auth** | JWT |
| **Logging** | Structlog |

---

## 6. Endpoints API v2

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v2/health` | Health check |
| POST | `/api/v2/auth/login` | Login |
| GET | `/api/v2/auth/me` | Perfil |
| POST | `/api/v2/chat` | Chat síncrono |
| POST | `/api/v2/chat/stream` | Chat SSE |
| GET | `/api/v2/agents` | Lista agentes |
| GET | `/api/v2/metrics` | Métricas |

---

## 7. Decisões Arquiteturais

| Decisão | Justificativa |
|---------|---------------|
| **8 Agentes vs 1 Monolítico** | Separação de responsabilidades, testabilidade |
| **Ports/Adapters** | Baixo acoplamento, substituibilidade |
| **DuckDB sobre SQL Server** | Performance analítica 10-100x superior |
| **Parquet sobre CSV** | Compressão 10x, queries colunares |
| **Gemini 2.5 Flash-Lite** | Custo-benefício, velocidade, capacidade |
