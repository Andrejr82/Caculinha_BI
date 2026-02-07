# Sistema de Memória Conversacional

**Versão:** 2.0  
**Data:** 2026-02-07

---

## 1. Visão Geral

Sistema híbrido de memória para contexto conversacional.

```
┌─────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │
│  │   Redis     │    │   SQLite    │    │  DuckDB    │  │
│  │  Short-term │    │  Long-term  │    │  Semantic  │  │
│  │  (TTL: 1h)  │    │ (Permanent) │    │  (Vector)  │  │
│  └──────┬──────┘    └──────┬──────┘    └─────┬──────┘  │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            ▼                            │
│                  ┌─────────────────┐                   │
│                  │  MemoryAgent    │                   │
│                  │  load / save    │                   │
│                  └─────────────────┘                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Tipos de Memória

| Tipo | Storage | TTL | Uso |
|------|---------|-----|-----|
| **Sessão** | Redis | 1h | Contexto imediato |
| **Conversa** | SQLite | Permanente | Histórico completo |
| **Semântica** | DuckDB | Permanente | Busca por similaridade |

---

## 3. Entidades

### Conversation
```python
@dataclass
class Conversation:
    id: str              # conv-uuid
    tenant_id: str       # Isolamento
    user_id: str         # Proprietário
    title: Optional[str] # Título auto-gerado
    created_at: datetime
    updated_at: datetime
```

### Message
```python
@dataclass
class Message:
    id: str              # msg-uuid
    conversation_id: str # FK
    role: str            # user | assistant | system
    content: str         # Conteúdo
    timestamp: datetime
    metadata: Optional[Dict]
```

### MemoryEntry
```python
@dataclass
class MemoryEntry:
    id: str              # mem-uuid
    conversation_id: str
    message_id: str
    content: str         # Texto indexado
    embedding: List[float]  # 768-dim
    score: float         # Relevância
```

---

## 4. Ports (Interfaces)

### IMemoryRepository
```python
class IMemoryRepository(ABC):
    async def save_conversation(self, conv: Conversation) -> str
    async def get_conversation(self, id: str) -> Optional[Conversation]
    async def add_message(self, msg: Message) -> str
    async def get_recent_messages(self, conv_id: str, limit: int) -> List[Message]
    async def delete_conversation(self, id: str) -> bool
    async def list_conversations(self, tenant_id: str) -> List[Conversation]
```

### IVectorRepository
```python
class IVectorRepository(ABC):
    async def index_entry(self, entry: MemoryEntry) -> str
    async def search_similar(self, embedding: List[float], limit: int) -> List[MemoryEntry]
    async def delete_by_conversation(self, conv_id: str) -> int
```

---

## 5. Adapters

| Port | Adapter | Tecnologia |
|------|---------|------------|
| IMemoryRepository | RedisMemoryAdapter | Redis (cache) |
| IMemoryRepository | SQLiteMemoryAdapter | SQLite (persistência) |
| IVectorRepository | DuckDBVectorAdapter | DuckDB + VSS |

---

## 6. Fluxo de Dados

### Load Memory
```
1. Request com conversation_id
2. Redis lookup (cache hit?)
   ├── HIT: Retorna contexto cached
   └── MISS: SQLite query
3. DuckDB semantic search (se query presente)
4. Merge: recent_messages + relevant_memories
5. Retorna MemoryContext
```

### Save Memory
```
1. Recebe user_message + assistant_response
2. Cria Message entities
3. SQLite: INSERT messages
4. Redis: UPDATE cache
5. DuckDB: INDEX embeddings (async)
```

---

## 7. Compressão de Contexto

```
┌────────────────────────────────────────┐
│         CompressionAgent               │
├────────────────────────────────────────┤
│ Quando: context_tokens > 4000          │
│ Como: Summarize mensagens antigas      │
│ Resultado: Contexto comprimido         │
└────────────────────────────────────────┘
```

---

## 8. Checklist

- [x] Entidades definidas
- [x] Ports definidos
- [x] Adapters identificados
- [x] Fluxo documentado
