# Mapa de Módulos — Caculinha BI Agent Platform

**Data:** 2026-02-07  
**Versão:** 1.0.0  
**Autor:** Arquiteto de Sistema

---

## Visão Geral

```
backend/app/
├── api/                    # PRESENTATION LAYER
│   └── v1/
│       ├── endpoints/      # 20 arquivos
│       └── router.py
│
├── core/                   # BUSINESS LOGIC (Misto)
│   ├── agents/             # Agentes IA
│   ├── tools/              # Ferramentas BI
│   ├── prompts/            # Templates de prompt
│   ├── llm_*.py            # Adapters LLM
│   ├── cache.py
│   └── ...
│
├── infrastructure/         # INFRASTRUCTURE LAYER
│   ├── database/
│   └── data/
│
├── services/               # APPLICATION SERVICES
│   └── *.py
│
├── schemas/                # PYDANTIC MODELS
│   └── *.py
│
└── orchestration/          # LANGGRAPH (Incompleto)
    └── graph.py
```

---

## Módulos Detalhados

### 1. API (Presentation Layer)

**Caminho:** `backend/app/api/v1/endpoints/`

| Módulo | Arquivo | Linhas | Responsabilidade |
|--------|---------|--------|------------------|
| Dashboard | `dashboard.py` | ~800 | Métricas consolidadas |
| Chat | `chat.py` | ~700 | BI conversacional |
| Metrics | `metrics.py` | ~550 | Métricas de negócio |
| Analytics | `analytics.py` | ~500 | Analytics avançado |
| Transfers | `transfers.py` | ~450 | Transferências |
| Learning | `learning.py` | ~450 | Sistema de aprendizado |
| Admin | `admin.py` | ~400 | Administração |
| Auth | `auth.py` | ~300 | Autenticação |
| Insights | `insights.py` | ~280 | Insights IA |
| Rupturas | `rupturas.py` | ~250 | Gestão de rupturas |
| Reports | `reports.py` | ~170 | Relatórios |
| Preferences | `preferences.py` | ~200 | Preferências |
| Playground | `playground.py` | ~220 | Sandbox |
| Health | `health.py` | ~200 | Health checks |
| Diagnostics | `diagnostics.py` | ~180 | Debug |
| Shared | `shared.py` | ~150 | Utils compartilhados |
| Frontend Logs | `frontend_logs.py` | ~130 | Logs do frontend |
| Code Chat | `code_chat.py` | ~190 | Chat de código |
| Auth Alt | `auth_alt.py` | ~90 | Auth alternativo |

---

### 2. Core — Agents

**Caminho:** `backend/app/core/agents/`

| Módulo | Arquivo | KB | Responsabilidade |
|--------|---------|------|------------------|
| **CaculinhaBIAgent** | `caculinha_bi_agent.py` | 69 | Orquestração BI completa (MONOLÍTICO) |
| BaseAgent | `base_agent.py` | 4 | Classe base abstrata |
| CodeGenAgent | `code_gen_agent.py` | 12 | Geração de código Python |
| PromptLoader | `prompt_loader.py` | 5 | Carregamento de prompts |

**Dependências:**
```
caculinha_bi_agent.py
├── imports from: tools/* (17 arquivos)
├── imports from: llm_gemini_adapter.py
├── imports from: data_source_manager.py
└── imports from: prompts/*
```

---

### 3. Core — Tools

**Caminho:** `backend/app/core/tools/`

| Módulo | Arquivo | KB | Categoria | Responsabilidade |
|--------|---------|------|----------|------------------|
| UNE Tools | `une_tools.py` | 73 | Análise | Multi-loja (MONOLÍTICO) |
| Chart Tools | `chart_tools.py` | 63 | Visual | Gráficos (MONOLÍTICO) |
| Universal Chart | `universal_chart_generator.py` | 22 | Visual | Gerador universal |
| Purchasing | `purchasing_tools.py` | 16 | Compras | EOQ, sugestões |
| Flexible Query | `flexible_query_tool.py` | 14 | Query | Consultas flex |
| Unified Data | `unified_data_tools.py` | 14 | Data | Unificação |
| Semantic Search | `semantic_search_tool.py` | 13 | Search | Busca semântica |
| Advanced Analytics | `advanced_analytics_tool.py` | 12 | STEM | Regressão, anomalias |
| Metadata | `metadata_tools.py` | 11 | Schema | Dicionário de dados |
| Code Interpreter | `code_interpreter.py` | 9 | Code | Execução Python |
| Quick Response | `quick_response.py` | 6 | Util | Respostas rápidas |
| MCP Parquet | `mcp_parquet_tools.py` | 6 | Data | MCP protocol |
| Anomaly Detection | `anomaly_detection.py` | 4 | STEM | Outliers |
| Offline Chart | `offline_chart_tool.py` | 4 | Visual | Gráficos offline |
| Date Time | `date_time_tools.py` | 1 | Util | Datas |

---

### 4. Core — LLM Adapters

**Caminho:** `backend/app/core/`

| Módulo | Arquivo | KB | Provider |
|--------|---------|------|----------|
| Gemini Adapter | `llm_gemini_adapter.py` | 39 | Google Gemini |
| GenAI Adapter | `llm_genai_adapter.py` | 31 | Google GenAI (legado) |
| LangChain Adapter | `llm_langchain_adapter.py` | 12 | LangChain |
| Groq Adapter | `llm_groq_adapter.py` | 8 | Groq |
| LLM Factory | `llm_factory.py` | 8 | Factory pattern |
| Mock | `llm_mock.py` | 6 | Testes |

---

### 5. Infrastructure

**Caminho:** `backend/app/infrastructure/`

| Módulo | Subpasta | Responsabilidade |
|--------|----------|------------------|
| Database | `database/` | Conexões, models |
| Data | `data/` | Adapters parquet, DuckDB |

---

### 6. Services

**Caminho:** `backend/app/services/`

| Arquivo | Responsabilidade |
|---------|------------------|
| `chat_service.py` | Lógica de chat |
| `insight_service.py` | Geração de insights |
| `llm_insights.py` | Insights via LLM |
| `metrics_calculator.py` | Cálculos de métricas |
| `data_aggregation.py` | Agregações |
| ... | ... |

---

### 7. Orchestration

**Caminho:** `backend/app/orchestration/`

| Arquivo | Status | Responsabilidade |
|---------|--------|------------------|
| `graph.py` | INCOMPLETO | LangGraph workflow |
| `nodes.py` | INCOMPLETO | Nós do grafo |
| `state.py` | INCOMPLETO | Estado do grafo |

---

## Diagrama de Dependências

```
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │dashboard│ │  chat   │ │ metrics │ │analytics│  ...          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘               │
└───────┼──────────┼──────────┼──────────┼────────────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CACULINHA_BI_AGENT (MONOLÍTICO)              │  │
│  │  • Intent Classification                                  │  │
│  │  • Tool Selection                                         │  │
│  │  • Query Execution                                        │  │
│  │  • Narrative Generation                                   │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               │                                 │
│  ┌────────────────────────────┼────────────────────────────┐   │
│  │                      TOOLS                              │   │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │ │une_tools │ │chart_tool│ │query_tool│ │analytics │    │   │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────┼────────────────────────────┐   │
│  │                   LLM ADAPTERS                          │   │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │   │
│  │ │  Gemini  │ │   Groq   │ │ LangChain│                 │   │
│  │ └──────────┘ └──────────┘ └──────────┘                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  DuckDB  │ │ Parquet  │ │SQL Server│ │ Supabase │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decomposição Proposta

### De (Atual):
```
caculinha_bi_agent.py (69 KB)
└── Todas as responsabilidades
```

### Para (Alvo):
```
agents/
├── orchestrator_agent.py    # Coordenação
├── sql_agent.py             # Queries
├── insight_agent.py         # Narrativas
├── forecast_agent.py        # Previsões
├── metadata_agent.py        # Schema
├── tenant_agent.py          # Multi-tenant
├── security_agent.py        # Auth/Audit
└── monitoring_agent.py      # Observabilidade
```

---

## Próximos Passos

1. **FASE 2:** Criar estrutura de pastas Clean Architecture
2. **FASE 3:** Definir contratos (Ports) para cada agente
3. **FASE 4:** Implementar código base funcional
4. **FASE 5:** MVP conversacional
5. **FASE 6:** SaaS-ready
