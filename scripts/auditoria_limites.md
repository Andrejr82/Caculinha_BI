# Auditoria de Limites Hardcoded - Agent Solution BI

## 🎯 Objetivo
Identificar todos os limites hardcoded que podem restringir respostas do agente.

---

## 📊 Limites Encontrados

### ✅ CORRIGIDOS (Sessão Atual)

| Arquivo | Linha | Antes | Depois | Status |
|---------|-------|-------|--------|--------|
| `flexible_query_tool.py` | 75 | 20 | 100 | ✅ Corrigido |
| `flexible_query_tool.py` | 97-101 | 50 (max) | 500 (max) | ✅ Corrigido |
| `universal_chart_generator.py` | 80-82 | 10 | 100 | ✅ Corrigido |

---

### ⚠️ CRÍTICOS (Precisam Correção)

| Arquivo | Linha | Limite | Impacto | Prioridade |
|---------|-------|--------|---------|------------|
| `unified_data_tools.py` | 204 | `limite: int = 10` | **ALTO** - Ferramenta de análise | 🔴 CRÍTICO |
| `offline_chart_tool.py` | 21 | `limite: int = 10` | **MÉDIO** - Gráficos offline | 🟡 MÉDIO |
| `semantic_search_tool.py` | 171 | `limite: int = 10` | **BAIXO** - Busca semântica | 🟢 BAIXO |

---

### 📝 ACEITÁVEIS (Contexto Específico)

| Arquivo | Linha | Limite | Justificativa |
|---------|-------|--------|---------------|
| `une_tools.py` | 737 | `limite: int = 20` | Transferências (top 20 é razoável) |
| `une_tools.py` | 1037 | `limite: int = 50` | Produtos sem vendas (50 é suficiente) |
| `une_tools.py` | 1150 | `limite: int = 100` | Rupturas críticas (100 é bom) |
| `une_tools.py` | 1296 | `limite: int = 20` | Análise específica |
| `chart_tools.py` | 101 | `limite: int = 10` | **DEPRECATED** (usar `universal_chart_generator`) |
| `purchasing_tools.py` | 82, 221, 329 | `LIMIT 1` | Lookup de produto único (correto) |
| `code_interpreter.py` | 166 | `.head(50)` | Preview de dados (50 é razoável) |

---

### 🔍 HARDCODED (Não Parametrizável)

| Arquivo | Linha | Código | Impacto |
|---------|-------|--------|---------|
| `une_tools.py` | 289 | `df_abastecer.head(20)` | Top 20 produtos para abastecer |
| `une_tools.py` | 869 | `.head(5)` | Top 5 origens de transferência |
| `une_tools.py` | 885 | `.head(3)` | Top 3 destinos de transferência |
| `une_tools.py` | 1593 | `.nlargest(5, col_vendas)` | Top 5 lojas |
| `une_tools.py` | 1611 | `.head(10)` | Top 10 lojas em ruptura |
| `chart_tools.py` | 1344, 1371, 1396 | `.head(10)` | Top 10 grupos (gráficos) |
| `chart_tools.py` | 1633 | `.sample(2000)` | Amostragem de 2000 pontos |
| `universal_chart_generator.py` | 166 | `LIMIT 50` | Fallback SQL (se limite=None) |

---

## 🚨 CORREÇÕES PRIORITÁRIAS

### 1. `unified_data_tools.py` - Linha 204 (CRÍTICO)

**Problema:** Ferramenta de análise com limite de **10** resultados.

**Arquivo:** `backend/app/core/tools/unified_data_tools.py`

**Código Atual:**
```python
limite: int = 10  # ❌ Muito baixo!
```

**Correção Recomendada:**
```python
limite: int = 100  # ✅ Consistente com outras ferramentas
```

**Impacto:** **ALTO** - Afeta análises gerais do agente.

---

### 2. `offline_chart_tool.py` - Linha 21 (MÉDIO)

**Problema:** Gráficos offline limitados a **10** itens.

**Arquivo:** `backend/app/core/tools/offline_chart_tool.py`

**Código Atual:**
```python
limite: int = 10  # ❌ Muito baixo
```

**Correção Recomendada:**
```python
limite: int = 100  # ✅ Consistente
```

**Impacto:** **MÉDIO** - Afeta gráficos gerados offline.

---

### 3. `semantic_search_tool.py` - Linha 171 (BAIXO)

**Problema:** Busca semântica limitada a **10** resultados.

**Arquivo:** `backend/app/core/tools/semantic_search_tool.py`

**Código Atual:**
```python
limite: int = 10  # ❌ Pode ser baixo para buscas amplas
```

**Correção Recomendada:**
```python
limite: int = 50  # ✅ Mais resultados para busca semântica
```

**Impacto:** **BAIXO** - Busca semântica é menos usada.

---

## 📋 Recomendações

### Padrões Sugeridos

| Tipo de Ferramenta | Limite Padrão | Limite Máximo |
|--------------------|---------------|---------------|
| **Consulta de Dados** | 100 | 500 |
| **Gráficos** | 100 | 500 |
| **Análises** | 100 | 500 |
| **Busca Semântica** | 50 | 200 |
| **Transferências/Sugestões** | 20-50 | 100 |
| **Lookups Únicos** | 1 | 1 |
| **Previews** | 50 | 100 |

### Princípios

1. ✅ **Consistência:** Ferramentas similares devem ter limites similares
2. ✅ **Parametrizável:** Sempre permitir que o agente passe limite customizado
3. ✅ **Documentação:** Comentar o motivo do limite escolhido
4. ✅ **Fallback:** Sempre ter um limite máximo para proteção

---

## 🎯 Próximos Passos

1. **Corrigir CRÍTICOS:**
   - [ ] `unified_data_tools.py` linha 204: 10 → 100
   - [ ] `offline_chart_tool.py` linha 21: 10 → 100

2. **Revisar MÉDIOS:**
   - [ ] `semantic_search_tool.py` linha 171: 10 → 50

3. **Documentar ACEITÁVEIS:**
   - [ ] Adicionar comentários explicando por que 20/50 é adequado

4. **Refatorar HARDCODED:**
   - [ ] Transformar `.head(N)` em parâmetros quando fizer sentido

---

## 📊 Estatísticas

- **Total de limites encontrados:** 35+
- **Críticos (precisam correção):** 3
- **Aceitáveis (contexto específico):** 10
- **Hardcoded (não parametrizável):** 10+
- **Já corrigidos:** 3

---

## ✅ Conclusão

**Principais Problemas:**
1. `unified_data_tools.py` com limite de **10** (CRÍTICO)
2. `offline_chart_tool.py` com limite de **10** (MÉDIO)
3. Falta de consistência entre ferramentas

**Após correções:**
- Agente poderá responder com dados completos
- Gráficos mostrarão todos os resultados relevantes
- Consistência entre todas as ferramentas
