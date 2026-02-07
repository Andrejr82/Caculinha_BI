# Definição de Agentes

**Versão:** 2.0  
**Data:** 2026-02-07

---

## 1. Catálogo de Agentes

| # | Agente | Responsabilidade |
|---|--------|------------------|
| 1 | OrchestratorAgent | Coordena pipeline cognitivo |
| 2 | MemoryAgent | Load/Save memória conversacional |
| 3 | VectorizationAgent | Gera embeddings |
| 4 | RankingAgent | Ranking híbrido BM25+Neural |
| 5 | RAGAgent | Retrieve-Augment-Generate |
| 6 | CompressionAgent | Comprime contexto longo |
| 7 | FeatureStoreAgent | Gestão de features |
| 8 | SQLAgent | Executa queries analíticas |
| 9 | InsightAgent | Gera insights de negócio |

---

## 2. Pipeline Cognitivo

```
User Query
    │
    ├──→ CompressionAgent (se contexto > 4000 tokens)
    │
    ├──→ MemoryAgent.load_memory()
    │
    ├──→ VectorizationAgent.vectorize(query)
    │
    ├──→ RankingAgent.rank(query, documents)
    │
    ├──→ RAGAgent.retrieve_and_generate()
    │
    ├──→ InsightAgent.generate_insight()
    │
    └──→ MemoryAgent.save_memory()
```

---

## 3. Especificação por Agente

### 3.1 OrchestratorAgent
```python
class OrchestratorAgent(BaseAgent):
    """
    Agente central que coordena o pipeline.
    
    Capabilities:
    - intent_classification
    - agent_selection
    - workflow_coordination
    - response_synthesis
    - memory_management
    
    Tools:
    - classificar_intencao
    - selecionar_agentes
    - carregar_memoria
    """
```

### 3.2 MemoryAgent
```python
class MemoryAgent(BaseAgent):
    """
    Gerencia memória conversacional.
    
    Capabilities:
    - load_memory
    - save_memory
    - search_memories
    - create_conversation
    - delete_conversation
    
    Dependencies:
    - IMemoryRepository
    - IVectorRepository (opcional)
    """
```

### 3.3 VectorizationAgent
```python
class VectorizationAgent(BaseAgent):
    """
    Gera embeddings para textos.
    
    Capabilities:
    - vectorize_text
    - batch_vectorize
    
    Dependencies:
    - Gemini Embedding API
    """
```

### 3.4 RankingAgent
```python
class RankingAgent(BaseAgent):
    """
    Ranking híbrido de documentos.
    
    Capabilities:
    - bm25_rank
    - neural_rank
    - reciprocal_rank_fusion
    
    Dependencies:
    - IRankingPort
    """
```

### 3.5 RAGAgent
```python
class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation.
    
    Capabilities:
    - retrieve_documents
    - augment_prompt
    - generate_response
    
    Dependencies:
    - IVectorRepository
    - LLMPort
    """
```

### 3.6 CompressionAgent
```python
class CompressionAgent(BaseAgent):
    """
    Comprime contexto longo.
    
    Capabilities:
    - summarize_messages
    - compress_context
    
    Dependencies:
    - ICompressionPort
    """
```

### 3.7 FeatureStoreAgent
```python
class FeatureStoreAgent(BaseAgent):
    """
    Gestão de features para ML.
    
    Capabilities:
    - store_feature
    - get_feature
    - list_features
    
    Dependencies:
    - IFeatureStore
    """
```

### 3.8 SQLAgent
```python
class SQLAgent(BaseAgent):
    """
    Executa queries analíticas.
    
    Capabilities:
    - execute_query
    - explain_query
    - validate_query
    
    Dependencies:
    - DuckDB / SQL Server
    """
```

### 3.9 InsightAgent
```python
class InsightAgent(BaseAgent):
    """
    Gera insights de negócio.
    
    Capabilities:
    - generate_insight
    - detect_anomalies
    - suggest_actions
    
    Dependencies:
    - LLMPort
    """
```

---

## 4. Matriz de Dependências

```
                    ┌───────────────────────────────────────┐
                    │         OrchestratorAgent             │
                    └───────────────┬───────────────────────┘
                                    │
        ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
        │           │           │       │           │           │
        ▼           ▼           ▼       ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │Memory  │  │Vector  │  │Ranking │ │RAG     │ │Insight │ │SQL     │
   │Agent   │  │Agent   │  │Agent   │ │Agent   │ │Agent   │ │Agent   │
   └───┬────┘  └───┬────┘  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
       │           │           │          │          │          │
       ▼           ▼           ▼          ▼          ▼          ▼
   ┌────────┐  ┌────────┐  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │IMemory │  │Gemini  │  │IRanking│ │IVector │ │LLM     │ │DuckDB  │
   │Repo    │  │Embed   │  │Port    │ │Repo    │ │Port    │ │        │
   └────────┘  └────────┘  └────────┘ └────────┘ └────────┘ └────────┘
```

---

## 5. Checklist

- [x] Catálogo de agentes definido
- [x] Pipeline cognitivo documentado
- [x] Especificações individuais
- [x] Matriz de dependências
