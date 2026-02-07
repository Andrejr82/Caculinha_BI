# Diagnóstico Técnico — Caculinha BI Agent Platform

**Data:** 2026-02-07  
**Versão:** 1.0.0  
**Autor:** Arquiteto de Sistema

---

## 1. Visão Geral do Projeto

| Aspecto | Valor |
|---------|-------|
| **Nome** | Agent Solution BI (Caculinha BI) |
| **Propósito** | Plataforma de BI Conversacional para Varejo |
| **Cliente** | Lojas Caçula |
| **Status** | MVP Funcional |

---

## 2. Stack Técnica Identificada

### 2.1 Backend

| Componente | Tecnologia | Versão/Notas |
|------------|------------|--------------|
| **Runtime** | Python | 3.11+ |
| **Framework** | FastAPI | Async-first |
| **Motor de Dados** | DuckDB | ≥1.1.0 |
| **Armazenamento** | Apache Parquet | 55 arquivos |
| **ORM** | SQLAlchemy | 2.0 (async) |
| **Auth** | JWT + Supabase | Híbrido |
| **LLM Primário** | Google Gemini | google-genai ≥1.60.0 |
| **LLM Secundário** | Groq (Llama-3) | Fallback |
| **Logging** | Structlog | JSON estruturado |
| **Rate Limiting** | SlowAPI | - |

### 2.2 Frontend

| Componente | Tecnologia |
|------------|------------|
| **Framework** | SolidJS |
| **Bundler** | Vite |
| **Estilização** | Tailwind CSS |
| **Testes E2E** | Playwright |

### 2.3 Infraestrutura

| Componente | Tecnologia |
|------------|------------|
| **Banco Relacional** | SQL Server (híbrido) + SQLite (fallback) |
| **Migrações** | Alembic |
| **Servidor ASGI** | Uvicorn + Gunicorn |

---

## 3. Estrutura de Diretórios

```
C:\Projetos_BI\BI_Solution\
├── .agent/                         # Antigravity Kit
│   ├── agents/                     # 19 agentes especialistas
│   ├── skills/                     # 121 arquivos de skills
│   ├── workflows/                  # 11 workflows
│   └── ARCHITECTURE.md
│
├── backend/                        # Backend Python
│   ├── app/                        # Código principal (196 arquivos)
│   │   ├── api/v1/endpoints/       # 20 endpoints REST
│   │   ├── core/                   # Núcleo (89 arquivos)
│   │   │   ├── agents/             # Agentes de IA (6 arquivos)
│   │   │   ├── tools/              # Ferramentas BI (17 arquivos)
│   │   │   └── llm_*.py            # Adapters LLM
│   │   ├── infrastructure/         # Persistência (23 arquivos)
│   │   ├── orchestration/          # LangGraph (3 arquivos)
│   │   ├── services/               # Serviços (10 arquivos)
│   │   └── schemas/                # Pydantic (5 arquivos)
│   ├── data/                       # Dados Parquet (55 arquivos)
│   ├── tests/                      # Testes (93 arquivos)
│   ├── main.py                     # Entry point FastAPI
│   └── requirements.txt            # 46 dependências
│
└── frontend-solid/                 # Frontend SolidJS
    ├── src/                        # Código fonte
    └── playwright.config.ts
```

---

## 4. Pontos de Entrada

| Tipo | Caminho | Descrição |
|------|---------|-----------|
| **Backend Entry** | `backend/main.py` | FastAPI app com lifespan async |
| **API Router** | `backend/app/api/v1/router.py` | Roteamento REST |
| **Agente Principal** | `backend/app/core/agents/caculinha_bi_agent.py` | Lógica BI conversacional |
| **Prompt Sistema** | `backend/app/core/agents/prompt_loader.py` | Context7 Ultimate |

---

## 5. Componentes Mapeados

### 5.1 Agentes de IA

| Arquivo | Tamanho | Responsabilidade |
|---------|---------|------------------|
| `caculinha_bi_agent.py` | **69 KB** | Orquestração BI (MONOLÍTICO) |
| `base_agent.py` | 4 KB | Classe base |
| `code_gen_agent.py` | 12 KB | Geração de código |

### 5.2 Ferramentas de BI

| Arquivo | Tamanho | Responsabilidade |
|---------|---------|------------------|
| `une_tools.py` | **73 KB** | Análise multi-loja (MONOLÍTICO) |
| `chart_tools.py` | **63 KB** | Visualização (MONOLÍTICO) |
| `purchasing_tools.py` | 16 KB | EOQ e compras |
| `flexible_query_tool.py` | 14 KB | Consultas flexíveis |
| `unified_data_tools.py` | 14 KB | Dados unificados |
| `advanced_analytics_tool.py` | 12 KB | STEM analytics |
| `semantic_search_tool.py` | 13 KB | Busca semântica |
| `metadata_tools.py` | 11 KB | Dicionário de dados |
| `code_interpreter.py` | 9 KB | Execução de código |
| `quick_response.py` | 6 KB | Respostas rápidas |
| `mcp_parquet_tools.py` | 6 KB | MCP Parquet |
| `anomaly_detection.py` | 4 KB | Detecção anomalias |
| `offline_chart_tool.py` | 4 KB | Gráficos offline |

### 5.3 Endpoints API

| Arquivo | Tamanho | Endpoints |
|---------|---------|-----------|
| `dashboard.py` | 31 KB | Dashboard metrics |
| `chat.py` | 28 KB | Chat conversacional |
| `metrics.py` | 21 KB | Métricas de negócio |
| `analytics.py` | 20 KB | Analytics avançado |
| `transfers.py` | 18 KB | Transferências |
| `learning.py` | 18 KB | Aprendizado |
| `admin.py` | 16 KB | Administração |
| `auth.py` | 11 KB | Autenticação |
| `insights.py` | 11 KB | Insights IA |
| `rupturas.py` | 9 KB | Gestão rupturas |

---

## 6. Dependências (requirements.txt)

### 6.1 Core

| Dependência | Uso |
|-------------|-----|
| `fastapi` | Framework web |
| `uvicorn[standard]` | Servidor ASGI |
| `pydantic>=2.0` | Validação |
| `sqlalchemy` | ORM |
| `duckdb>=1.1.0` | Motor analítico |

### 6.2 LLM/IA

| Dependência | Uso |
|-------------|-----|
| `google-genai>=1.60.0` | Gemini SDK (2026) |
| `groq` | LLM secundário |
| `langchain` | Orquestração |
| `langchain-google-genai` | Adapter LangChain |
| `langgraph` | Grafos de agentes |

### 6.3 Dados

| Dependência | Uso |
|-------------|-----|
| `pandas` | DataFrames |
| `polars` | DataFrames performáticos |
| `pyarrow` | Parquet I/O |
| `numpy` | Numérico |

---

## 7. Métricas do Projeto

| Métrica | Valor |
|---------|-------|
| **Total de arquivos backend** | 585 |
| **Arquivos em app/** | 196 |
| **Arquivos na raiz backend/** | 104 ⚠️ |
| **Dependências Python** | 46 |
| **Endpoints API** | 20 |
| **Ferramentas BI** | 17 |
| **Agentes IA** | 3 |
| **Testes** | 93 arquivos |
| **Arquivos Parquet (dados)** | 55 |
| **Agentes Antigravity** | 19 |
| **Skills Antigravity** | 121 |
| **Workflows Antigravity** | 11 |

---

## 8. Conclusão

O projeto é um **MVP funcional** com features ricas de BI conversacional. Entretanto, sofre de:

1. **Arquivos monolíticos** (agente de 69KB, ferramentas de 73KB)
2. **Arquivos soltos na raiz** (104 arquivos de teste/diagnóstico)
3. **Ausência de separação de camadas** (Domain/Application/Infrastructure)
4. **Sem multi-tenancy** nativo

Recomenda-se **decomposição em 8 agentes especializados** seguindo Clean Architecture.
