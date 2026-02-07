# Arquitetura de Memória Conversacional

**Data:** 2026-02-07  
**Workflow:** /brainstorm  
**Agente Líder:** backend-specialist

---

## 🧠 Brainstorm: Sistema de Memória Conversacional

### Contexto

A plataforma Caculinha BI precisa de **memória persistente** para conversas, permitindo:
- Carregar contexto antes de responder
- Salvar contexto após resposta
- Busca semântica em histórico
- Multi-tenancy

---

## Opção A: Redis + DuckDB Vector

**Descrição:** Redis para memória de curto prazo (sessão), DuckDB para memória de longo prazo com busca vetorial.

```
┌─────────────────────────────────────────────────────────────┐
│                      MEMORY LAYER                           │
│                                                             │
│  ┌─────────────────┐      ┌─────────────────────────────┐  │
│  │  Redis (TTL)    │      │  DuckDB + Vector Extension  │  │
│  │  ─────────────  │      │  ─────────────────────────  │  │
│  │  • Session      │      │  • Long-term history        │  │
│  │  • Last N msgs  │      │  • Semantic search          │  │
│  │  • Cache        │      │  • Embeddings               │  │
│  └─────────────────┘      └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

✅ **Prós:**
- Performance excelente (Redis in-memory)
- DuckDB já está no projeto
- Busca vetorial nativa (duckdb-vss)
- Sem dependências novas

❌ **Contras:**
- Redis requer servidor separado
- Complexidade de sincronização

📊 **Esforço:** Médio

---

## Opção B: SQLite + FAISS

**Descrição:** SQLite para persistência, FAISS para busca vetorial.

✅ **Prós:**
- SQLite é zero-config
- FAISS é muito rápido

❌ **Contras:**
- Duas tecnologias separadas
- FAISS não persiste nativamente
- Sync complexo

📊 **Esforço:** Alto

---

## Opção C: SQLite Unificado (Simples)

**Descrição:** SQLite como única fonte de dados, com busca por texto e similaridade via distância coseno.

```
┌─────────────────────────────────────────────────────────────┐
│                  SQLITE MEMORY STORE                        │
│                                                             │
│  conversations: id, tenant_id, created_at, updated_at       │
│  messages: id, conversation_id, role, content, timestamp    │
│  memory_entries: id, conversation_id, embedding, metadata   │
└─────────────────────────────────────────────────────────────┘
```

✅ **Prós:**
- Zero dependências externas
- Backup simples (arquivo único)
- Portabilidade total

❌ **Contras:**
- Busca vetorial mais lenta
- Menos escalável

📊 **Esforço:** Baixo

---

## 💡 Recomendação

**Opção A: Redis + DuckDB Vector** porque:

1. **Redis já existe** em muitos deploys de produção
2. **DuckDB** já está integrado no projeto
3. **Performance** excelente para ambos cenários
4. **Fallback SQLite** para dev local sem Redis

### Arquitetura Híbrida Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                     MEMORY AGENT                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MemoryRepositoryPort                    │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • save_conversation(conv: Conversation)            │   │
│  │  • get_conversation(id: str) -> Conversation        │   │
│  │  • list_conversations(tenant_id: str) -> List       │   │
│  │  • delete_conversation(id: str)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│           ┌────────────────┼────────────────┐              │
│           │                │                │              │
│           ▼                ▼                ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │RedisMemory   │  │SQLiteMemory  │  │DuckDBVector      │  │
│  │Adapter       │  │Adapter       │  │SearchAdapter     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Ports Definidos

### MemoryRepositoryPort
```python
class MemoryRepositoryPort(ABC):
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> str: ...
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]: ...
    
    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message) -> None: ...
    
    @abstractmethod
    async def get_messages(self, conversation_id: str, limit: int = 10) -> List[Message]: ...
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool: ...
```

### VectorSearchPort
```python
class VectorSearchPort(ABC):
    @abstractmethod
    async def index_message(self, message: Message, embedding: List[float]) -> None: ...
    
    @abstractmethod
    async def search_similar(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        tenant_id: Optional[str] = None
    ) -> List[MemoryEntry]: ...
    
    @abstractmethod
    async def delete_by_conversation(self, conversation_id: str) -> int: ...
```

---

## Entidades de Domínio

### Conversation
```python
@dataclass
class Conversation:
    id: str
    tenant_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    messages: List[Message] = field(default_factory=list)
```

### Message
```python
@dataclass
class Message:
    id: str
    conversation_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
```

### MemoryEntry
```python
@dataclass
class MemoryEntry:
    id: str
    conversation_id: str
    message_id: str
    content: str
    embedding: List[float]
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
```

---

## Decisão Final

| Componente | Tecnologia |
|------------|------------|
| **Short-term Memory** | Redis (com fallback SQLite) |
| **Long-term Memory** | SQLite |
| **Vector Search** | DuckDB VSS Extension |
| **Embeddings** | Gemini Embedding API |

---

**Próximo:** Criar `docs/memory_flow.md` com fluxo de dados.
