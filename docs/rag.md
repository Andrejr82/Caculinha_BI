# Sistema RAG (Retrieval-Augmented Generation)

**Versão:** 2.0  
**Data:** 2026-02-07

---

## 1. Visão Geral

Pipeline RAG com ranking híbrido para BI conversacional.

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Query ───→ [Vectorize] ───→ [Retrieve] ───→ [Rank]        │
│                                     │            │          │
│                                     ▼            ▼          │
│                              ┌───────────┐ ┌──────────┐     │
│                              │ BM25      │ │ Neural   │     │
│                              │ (Sparse)  │ │ (Dense)  │     │
│                              └─────┬─────┘ └────┬─────┘     │
│                                    │            │           │
│                                    └─────┬──────┘           │
│                                          ▼                  │
│                                   [Reciprocal Rank]         │
│                                          │                  │
│                                          ▼                  │
│                                   [Top-K Contexts]          │
│                                          │                  │
│                                          ▼                  │
│                                    [LLM Generate]           │
│                                          │                  │
│                                          ▼                  │
│                                      Response               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes

### 2.1 VectorizationAgent
```python
class VectorizationAgent:
    """Gera embeddings para textos."""
    
    async def vectorize(self, text: str) -> List[float]:
        """Retorna embedding 768-dim via Gemini API."""
        
    async def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        """Vetorização em lote para ingestão."""
```

### 2.2 RankingAgent
```python
class RankingAgent:
    """Ranking híbrido BM25 + Neural."""
    
    async def rank(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[RankedDocument]:
        """
        1. BM25 score (sparse)
        2. Cosine similarity (dense)
        3. Reciprocal Rank Fusion
        """
```

### 2.3 RAGAgent
```python
class RAGAgent:
    """Orquestra retrieve + generate."""
    
    async def retrieve_and_generate(
        self,
        query: str,
        context: MemoryContext
    ) -> str:
        """
        1. Retrieve: Busca documentos relevantes
        2. Augment: Injeta no prompt
        3. Generate: LLM produz resposta
        """
```

---

## 3. Entidades RAG

### Document
```python
@dataclass
class Document:
    id: str
    tenant_id: str
    content: str
    source: str           # parquet, csv, manual
    chunk_index: int      # Posição do chunk
    metadata: Dict
    created_at: datetime
```

### Embedding
```python
@dataclass
class Embedding:
    id: str
    document_id: str
    vector: List[float]   # 768-dim
    model: str            # gemini-embedding-001
```

---

## 4. Ports RAG

### IRankingPort
```python
class IRankingPort(ABC):
    async def rank_documents(
        self, 
        query: str, 
        documents: List[Document],
        top_k: int = 5
    ) -> List[Tuple[Document, float]]
```

### ICompressionPort
```python
class ICompressionPort(ABC):
    async def compress_context(
        self, 
        messages: List[Message],
        max_tokens: int = 2000
    ) -> str
```

---

## 5. Adapters RAG

| Port | Adapter | Implementação |
|------|---------|---------------|
| IRankingPort | BM25RankingAdapter | rank-bm25 |
| IRankingPort | NeuralRankingAdapter | Cross-encoder (futuro) |
| ICompressionPort | LLMCompressionAdapter | Gemini summarization |

---

## 6. Reciprocal Rank Fusion

```python
def reciprocal_rank_fusion(
    bm25_ranks: List[Tuple[str, int]],
    neural_ranks: List[Tuple[str, int]],
    k: int = 60
) -> List[str]:
    """
    RRF(d) = Σ 1 / (k + rank_i(d))
    
    Combina rankings de múltiplos sistemas.
    """
    scores = defaultdict(float)
    
    for doc_id, rank in bm25_ranks:
        scores[doc_id] += 1 / (k + rank)
    
    for doc_id, rank in neural_ranks:
        scores[doc_id] += 1 / (k + rank)
    
    return sorted(scores, key=scores.get, reverse=True)
```

---

## 7. Ingestão de Documentos

```
┌────────────────────────────────────────────────────────────┐
│                    INGEST PIPELINE                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  File Upload ───→ [Parse] ───→ [Chunk] ───→ [Vectorize]   │
│                      │            │             │          │
│                      ▼            ▼             ▼          │
│                  Extract      Split by      Generate       │
│                  Text         512 tokens    Embeddings     │
│                                                            │
│                                       │                    │
│                                       ▼                    │
│                               [Store in DuckDB]            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 8. Checklist

- [x] Pipeline RAG definido
- [x] Ranking híbrido documentado
- [x] Entidades definidas
- [x] Ports definidos
