# Caculinha BI Enterprise - Arquitetura Geral

**Versão:** 2.0  
**Data:** 2026-02-07  
**Autor:** Project Planner Agent

---

## 1. Visão Geral

Plataforma de BI Conversacional com IA Generativa para varejo.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACULINHA BI ENTERPRISE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │ Frontend│───→│ API Gateway │───→│   Cognitive Pipeline    │ │
│  │ SolidJS │    │   FastAPI   │    │                         │ │
│  └─────────┘    └─────────────┘    │  Compression → Memory   │ │
│                                     │  → Vector → Ranking    │ │
│                                     │  → RAG → Insight       │ │
│                                     └─────────────────────────┘ │
│                                                │                │
│            ┌───────────────────────────────────┼────────────┐  │
│            │              DATA LAYER           │            │  │
│            │                                   ▼            │  │
│  ┌─────────┴──────┐  ┌──────────────┐  ┌──────────────────┐ │  │
│  │ Redis (Cache)  │  │ SQLite/PG    │  │ DuckDB (Vector)  │ │  │
│  │ Short-term     │  │ Long-term    │  │ Feature Store    │ │  │
│  └────────────────┘  └──────────────┘  └──────────────────┘ │  │
│            └───────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **LLM** | Google Gemini 2.5 Pro | Raciocínio STEM, tool calling nativo |
| **Backend** | FastAPI + Python 3.11 | Async, tipagem forte |
| **Frontend** | SolidJS | Reatividade sem Virtual DOM |
| **Cache** | Redis | Sub-millisegundo, TTL nativo |
| **Persistência** | SQLite → PostgreSQL | Dev → Prod migration path |
| **Vetorial** | DuckDB + VSS | Busca semântica local |
| **Embeddings** | Gemini Embedding API | Consistência com LLM |

---

## 3. Princípios Arquiteturais

### 3.1 Hexagonal Architecture (Ports & Adapters)
```
┌────────────────────────────────────────────────────────┐
│                      DOMAIN                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Entities: Conversation, Message, MemoryEntry    │  │
│  │  Ports: IMemoryRepository, IVectorRepository     │  │
│  └──────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│                    APPLICATION                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Agents: Orchestrator, Memory, RAG, Insight      │  │
│  │  Services: ChatService, IngestService            │  │
│  └──────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Adapters: RedisAdapter, SQLiteAdapter, DuckDB   │  │
│  │  API: FastAPI Routers                            │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 3.2 Context7 Ultimate Pattern
- Narrativa primeiro (sem JSON bruto para usuário)
- Tool calling autônomo
- Autocorreção com dicionário de dados

### 3.3 Multi-Tenancy
- Tenant isolation via JWT claims
- Row-level security
- Per-tenant rate limiting

---

## 4. Pipeline Cognitivo

```
User Query
    │
    ▼
┌─────────────────┐
│ CompressionAgent│ → Sumariza contexto longo
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MemoryAgent     │ → Load: histórico + relevantes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ VectorizationAgt│ → Gera embeddings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RankingAgent    │ → BM25 + Neural Rerank
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RAGAgent        │ → Retrieve + Augment
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ InsightAgent    │ → Gera resposta final
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MemoryAgent     │ → Save: salva interação
└─────────────────┘
         │
         ▼
    Response
```

---

## 5. Estrutura de Diretórios

```
backend/
├── domain/
│   ├── entities/       # Conversation, Message, MemoryEntry, Document, Embedding
│   └── ports/          # IMemoryRepository, IVectorRepository, IRankingPort
├── application/
│   └── agents/         # OrchestratorAgent, MemoryAgent, RAGAgent...
├── infrastructure/
│   └── adapters/       # Redis, SQLite, DuckDB, BM25
├── api/
│   └── v1/endpoints/   # chat.py, ingest.py, memory.py
└── main.py
```

---

## 6. Checklist FASE 1

- [x] `docs/architecture.md` — Este documento
- [ ] `docs/memory.md` — Sistema de memória
- [ ] `docs/rag.md` — Retrieval-Augmented Generation
- [ ] `docs/agents.md` — Definição de agentes
- [ ] `docs/security.md` — Segurança e multi-tenancy
