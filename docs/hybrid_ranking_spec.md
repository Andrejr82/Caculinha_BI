# Especificação Técnica: Ranking Híbrido Avançado

Este documento define a estratégia de busca e ranqueamento (Retrieval & Ranking) para a plataforma de BI.

## 1. Estratégia de Indexação

Utilizaremos duas abordagens complementares para garantir precisão lexical e semântica.

### 1.1 Busca Lexical (BM25)
- **Engine:** Implementação via DuckDB ou scikit-learn (persistido).
- **Foco:** Correspondência exata de termos, marcas e modelos.
- **Atributos:** `name_canonical`, `brand`, `subcategory`.

### 1.2 Busca Semântica (Vector Search)
- **Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (ou similar otimizado para pt-BR).
- **Embeddings:** Gerados sobre o campo `searchable_text`.
- **Storage:** Vetores persistidos em DuckDB (coluna binária) ou arquivo FAISS.

## 2. Fusão de Ranking (Hybrid Score)

O score final de um produto será a combinação ponderada de diferentes sinais.

### 2.1 Fórmula de Fusão
`ScoreFinal = (w_bm25 * norm(BM25)) + (w_vec * norm(Vector)) + (w_rules * BusinessRulesBoost)`

**Pesos Iniciais Recomendados:**
- `w_bm25`: 0.55
- `w_vec`: 0.35
- `w_rules`: 0.10

## 3. Regras de Negócio e Boosts

Aplicadas após a recuperação inicial dos candidatos (Top 100).

| Regra | Tipo | Condição | Impacto |
|-------|------|----------|---------|
| Brand Match | Boost | Marca mencionada na query coincide com `brand` | +20% |
| Category Logic | Penalty | Catálogo indica categoria incompatível com contexto | -30% |
| Freshness | Boost | Produto com vendas recentes ou atualização nova | +5% |
| Out-of-Stock | Penalty | Produto sem estoque (se disponível no contexto RAG) | -50% |

## 4. Reranker (Opcional/Fallback)

Para o Top 20 final, utilizaremos o `reranker_agent`:
- **Semantic Reranking:** Reordenação baseada na intenção do usuário usando o modelo primário configurado no sistema (especificado no `.env`).
- **Heuristic Fallback:** Se a latência exceder 500ms ou houver erro, utiliza o ranking da fusão original baseada em regras de negócio.
- **Privacidade:** Nunca logar textos longos do catálogo ou dados sensíveis.

## 5. Métricas de Avaliação

A eficácia do ranking será monitorada através de:
- **Recall@K:** Capacidade de encontrar o produto correto entre os K primeiros.
- **MRR (Mean Reciprocal Rank):** Quão "em cima" o primeiro resultado relevante aparece.
- **nDCG (Normalized Discounted Cumulative Gain):** Qualidade global do ordenamento.

## 6. Feature Flag e Rollout

O ranking híbrido será controlado pela flag `ENABLE_HYBRID_RANKING`.
- **Default:** `false` (usa busca SQL direta).
- **Toggle:** Pode ser habilitado por Tenant para testes A/B.
