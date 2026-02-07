# Fluxo de Memória Conversacional

**Data:** 2026-02-07  
**Workflow:** /brainstorm  
**Agente Líder:** backend-specialist

---

## Fluxo de Dados

### 1. Fluxo de Requisição de Chat

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   Cliente   │────▶│  POST /chat     │────▶│  ProcessChatUseCase │
│   (HTTP)    │     │  Endpoint       │     │                     │
└─────────────┘     └─────────────────┘     └──────────┬──────────┘
                                                       │
                                                       ▼
                                            ┌──────────────────────┐
                                            │   OrchestratorAgent  │
                                            │   load_memory()      │◀─────┐
                                            └──────────┬───────────┘      │
                                                       │                   │
                              ┌─────────────────────────────────────────────┐
                              │                MEMORY AGENT                │
                              │                                             │
                              │  1. get_conversation(id)                   │
                              │  2. get_recent_messages(limit=10)          │
                              │  3. search_similar(query_embedding)        │
                              │                                             │
                              └─────────────────────────────────────────────┘
```

### 2. Fluxo de Carregamento de Memória (load_memory)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOAD MEMORY FLOW                                │
│                                                                         │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────┐ │
│  │ 1. Get Conv   │────▶│ 2. Get Recent │────▶│ 3. Vector Search      │ │
│  │    by ID      │     │    Messages   │     │    (if needed)        │ │
│  └───────────────┘     └───────────────┘     └───────────────────────┘ │
│         │                      │                        │               │
│         ▼                      ▼                        ▼               │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────┐ │
│  │ Conversation  │     │ Last 10 msgs  │     │ Top 5 relevant msgs   │ │
│  │ Metadata      │     │ (chronological)│     │ (semantic similarity) │ │
│  └───────────────┘     └───────────────┘     └───────────────────────┘ │
│                                                                         │
│  OUTPUT: Context object with:                                           │
│  - conversation_id                                                      │
│  - recent_messages (últimas N mensagens)                                │
│  - relevant_memories (mensagens semanticamente similares)               │
│  - tenant_context (plano, quotas)                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Fluxo de Salvamento de Memória (save_memory)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SAVE MEMORY FLOW                                │
│                                                                         │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────┐ │
│  │ 1. Save User  │────▶│ 2. Save LLM   │────▶│ 3. Index Embeddings   │ │
│  │    Message    │     │    Response   │     │    (async)            │ │
│  └───────────────┘     └───────────────┘     └───────────────────────┘ │
│         │                      │                        │               │
│         ▼                      ▼                        ▼               │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────┐ │
│  │ Redis (fast)  │     │ SQLite        │     │ DuckDB Vector         │ │
│  │ + SQLite      │     │ (persistent)  │     │ (searchable)          │ │
│  └───────────────┘     └───────────────┘     └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Integração com OrchestratorAgent

### Antes (sem memória)

```python
async def execute(self, task: str, context: Dict) -> Dict:
    # Apenas processa a mensagem atual
    result = await self._process_message(task)
    return result
```

### Depois (com memória)

```python
async def execute(self, task: str, context: Dict) -> Dict:
    # 1. LOAD: Carregar memória antes de processar
    memory_context = await self.memory_agent.load_memory(
        conversation_id=context.get("conversation_id"),
        query=task,
    )
    
    # 2. INJECT: Injetar contexto no prompt
    enriched_context = {
        **context,
        "recent_messages": memory_context.recent_messages,
        "relevant_memories": memory_context.relevant_memories,
    }
    
    # 3. PROCESS: Processar com contexto enriquecido
    result = await self._process_message(task, enriched_context)
    
    # 4. SAVE: Salvar resposta na memória
    await self.memory_agent.save_memory(
        conversation_id=context.get("conversation_id"),
        user_message=task,
        assistant_message=result["response"],
    )
    
    return result
```

---

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      OrchestratorAgent                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐│   │
│  │  │                      MemoryAgent                             ││   │
│  │  │  • load_memory(conversation_id, query) -> MemoryContext     ││   │
│  │  │  • save_memory(conversation_id, user_msg, assistant_msg)    ││   │
│  │  │  • search_memories(query, tenant_id) -> List[MemoryEntry]   ││   │
│  │  └─────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN LAYER                                 │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │  Conversation   │  │    Message      │  │     MemoryEntry         │ │
│  │  ────────────   │  │  ────────────   │  │  ────────────────────   │ │
│  │  id             │  │  id             │  │  id                     │ │
│  │  tenant_id      │  │  conversation_id│  │  conversation_id        │ │
│  │  user_id        │  │  role           │  │  embedding              │ │
│  │  messages[]     │  │  content        │  │  score                  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────┐  ┌──────────────────────────────┐ │
│  │   MemoryRepositoryPort          │  │   VectorSearchPort           │ │
│  │   ──────────────────────────    │  │   ────────────────────────   │ │
│  │   save_conversation()           │  │   index_message()            │ │
│  │   get_conversation()            │  │   search_similar()           │ │
│  │   add_message()                 │  │   delete_by_conversation()   │ │
│  │   get_messages()                │  │                              │ │
│  └─────────────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE LAYER                              │
│                                                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐   │
│  │ RedisMemoryAdapter│  │SQLiteMemoryAdapter│  │DuckDBVectorAdapter│   │
│  │ ────────────────  │  │ ────────────────  │  │ ────────────────  │   │
│  │ Implements:       │  │ Implements:       │  │ Implements:       │   │
│  │ MemoryRepoPort    │  │ MemoryRepoPort    │  │ VectorSearchPort  │   │
│  │                   │  │                   │  │                   │   │
│  │ Cache TTL: 1h     │  │ Persistent        │  │ VSS Extension     │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘   │
│           │                      │                      │               │
│           ▼                      ▼                      ▼               │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐   │
│  │      Redis        │  │     SQLite        │  │     DuckDB        │   │
│  │    (opcional)     │  │   memory.db       │  │   vectors.duckdb  │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Endpoints de Memória

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/memory/{conversation_id}` | Retorna histórico da conversa |
| DELETE | `/api/v1/memory/{conversation_id}` | Deleta conversa e histórico |
| GET | `/api/v1/memory/search` | Busca semântica em memórias |

---

## Verificação

### Testes Automatizados

```bash
# Testar MemoryAgent
pytest tests/test_memory_agent.py -v

# Testar Adapters
pytest tests/test_memory_adapters.py -v
```

### Critérios de Sucesso

- [ ] Salvar mensagem → mensagem persiste em SQLite
- [ ] Carregar conversa → retorna últimas N mensagens
- [ ] Busca vetorial → retorna mensagens relevantes
- [ ] Delete → remove conversa e embeddings
- [ ] Multi-tenant → isolamento de dados por tenant_id

---

**Próxima Fase:** FASE 2 — Criar entidades e ports no domínio.
