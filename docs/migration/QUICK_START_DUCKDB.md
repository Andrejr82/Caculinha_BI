# 🚀 Quick Start: Usando DuckDB Enhanced Adapter

**Para desenvolvedores que querem começar AGORA**

---

## ⚡ Uso Imediato

### Importar o Adapter

```python
from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

adapter = get_duckdb_adapter()
```

---

## 📖 Exemplos Práticos

### 1. Ler Parquet (Simples)

**ANTES** (Polars/Pandas):
```python
import polars as pl
df = pl.read_parquet("data/parquet/admmat.parquet")
```

**AGORA** (DuckDB):
```python
df = adapter.read_parquet("data/parquet/admmat.parquet")
```

**Benefício**: Mesma interface, 3x mais rápido!

---

### 2. Filtrar Dados

**ANTES** (Polars):
```python
df = pl.read_parquet("admmat.parquet")
df_filtered = df.filter(pl.col("estoque") > 0)
```

**AGORA** (DuckDB - Recomendado):
```python
df = adapter.query("""
    SELECT *
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE estoque > 0
""")
```

**Benefício**:
- Predicate pushdown (lê menos dados do disco)
- SQL mais claro que Python chaining

---

### 3. Agregação (Group By)

**ANTES** (Pandas):
```python
df = pd.read_parquet("admmat.parquet")
result = df.groupby('une')['estoque'].sum()
```

**AGORA** (DuckDB):
```python
result = adapter.query("""
    SELECT une, SUM(estoque) as total_estoque
    FROM read_parquet('data/parquet/admmat.parquet')
    GROUP BY une
""")
```

**Benefício**: Paralelo nativo (usa todos os cores)

---

### 4. Top N

**ANTES** (Polars):
```python
df = pl.read_parquet("admmat.parquet")
top10 = df.sort("venda_30dd", descending=True).head(10)
```

**AGORA** (DuckDB):
```python
top10 = adapter.query("""
    SELECT *
    FROM read_parquet('data/parquet/admmat.parquet')
    ORDER BY venda_30dd DESC
    LIMIT 10
""")
```

**Benefício**: Index scan (não precisa carregar tudo)

---

### 5. Múltiplas Colunas Específicas

**ANTES** (Pandas):
```python
df = pd.read_parquet("admmat.parquet", columns=['nome', 'estoque', 'venda_30dd'])
```

**AGORA** (DuckDB):
```python
df = adapter.read_parquet(
    "data/parquet/admmat.parquet",
    columns=['nome', 'estoque', 'venda_30dd']
)
```

**Benefício**: Column pruning automático

---

### 6. Join de Dados

**ANTES** (Pandas):
```python
df1 = pd.read_parquet("produtos.parquet")
df2 = pd.read_parquet("vendas.parquet")
result = df1.merge(df2, on='produto_id')
```

**AGORA** (DuckDB):
```python
result = adapter.query("""
    SELECT p.*, v.quantidade, v.valor
    FROM read_parquet('produtos.parquet') p
    JOIN read_parquet('vendas.parquet') v ON p.produto_id = v.produto_id
""")
```

**Benefício**: Hash join paralelo otimizado

---

### 7. Zero-Copy com Arrow

**Para máxima performance**:
```python
arrow_table = adapter.query_arrow("""
    SELECT * FROM read_parquet('admmat.parquet')
    WHERE estoque > 0
""")

# Arrow para Pandas (se necessário)
df = arrow_table.to_pandas()

# Arrow para lista de dicts
records = arrow_table.to_pylist()
```

**Benefício**: Zero cópia de memória

---

### 8. Cache de Resultados

**Para queries repetidas**:
```python
# Cache automático (LRU)
table_name = adapter.get_cached_parquet("admmat.parquet")

# Usar em queries
df = adapter.query(f"""
    SELECT * FROM {table_name}
    WHERE estoque > 0
""")
```

**Benefício**: Metadata cache persistente

---

### 9. Retornar Dict (API JSON)

**Para endpoints FastAPI**:
```python
records = adapter.query_dict("""
    SELECT une, nome, estoque
    FROM read_parquet('admmat.parquet')
    LIMIT 100
""")

# Retorna: [{"une": 1, "nome": "...", "estoque": 10}, ...]
return {"data": records}
```

**Benefício**: Zero conversões intermediárias

---

### 10. Schema de Parquet (Metadados)

**Descobrir colunas disponíveis**:
```python
schema = adapter.read_parquet_schema("admmat.parquet")
print(schema)
# {'id': 'BIGINT', 'nome': 'VARCHAR', 'estoque': 'DOUBLE', ...}
```

**Benefício**: Não carrega dados, apenas metadados

---

## 📊 Performance Monitoring

### Ver Métricas

```python
# Depois de executar várias queries
stats = adapter.get_metrics()
print(stats)
# {
#   'total_queries': 152,
#   'avg_duration_ms': 45.3,
#   'max_duration_ms': 320.1,
#   'min_duration_ms': 12.5,
#   'total_rows': 1_523_450
# }
```

### Reset Métricas

```python
adapter.reset_metrics()
```

---

## 🔧 Casos Avançados

### Async Queries

```python
async def get_data():
    result = await adapter.query_async("""
        SELECT * FROM read_parquet('admmat.parquet')
        WHERE estoque > 0
    """)
    return result
```

### Múltiplos Parquets (Glob)

```python
df = adapter.query("""
    SELECT * FROM read_parquet('data/parquet/*.parquet')
    WHERE data >= '2025-01-01'
""")
```

### Window Functions

```python
df = adapter.query("""
    SELECT
        nome,
        venda_30dd,
        ROW_NUMBER() OVER (ORDER BY venda_30dd DESC) as rank
    FROM read_parquet('admmat.parquet')
    WHERE venda_30dd > 0
""")
```

### CTEs (Common Table Expressions)

```python
df = adapter.query("""
    WITH vendas_altas AS (
        SELECT * FROM read_parquet('admmat.parquet')
        WHERE venda_30dd > 1000
    )
    SELECT une, COUNT(*) as total_produtos
    FROM vendas_altas
    GROUP BY une
""")
```

---

## ⚡ Benchmark Rápido

```python
import time

# Benchmark uma query
start = time.time()
df = adapter.query("SELECT * FROM read_parquet('admmat.parquet')")
print(f"Tempo: {(time.time() - start)*1000:.2f} ms")

# Ou usar método embutido
stats = adapter.benchmark(
    "SELECT COUNT(*) FROM read_parquet('admmat.parquet')",
    iterations=5
)
print(stats)
# {'avg_ms': 12.3, 'min_ms': 11.8, 'max_ms': 13.1}
```

---

## 🐛 Debugging

### Ver SQL Executado

```python
import logging
logging.getLogger("duckdb").setLevel(logging.DEBUG)
```

### Explicar Query Plan

```python
plan = adapter.connection.execute("""
    EXPLAIN SELECT * FROM read_parquet('admmat.parquet')
    WHERE estoque > 0
""").fetchall()
print(plan)
```

---

## 📝 Migração de Código Existente

### Polars → DuckDB

| Polars | DuckDB |
|--------|---------|
| `pl.read_parquet(path)` | `adapter.read_parquet(path)` |
| `df.filter(pl.col('x') > 10)` | `WHERE x > 10` |
| `df.select(['a', 'b'])` | `SELECT a, b` |
| `df.group_by('x').agg(pl.col('y').sum())` | `GROUP BY x, SUM(y)` |
| `df.sort('x', descending=True)` | `ORDER BY x DESC` |
| `df.head(10)` | `LIMIT 10` |

### Pandas → DuckDB

| Pandas | DuckDB |
|--------|---------|
| `pd.read_parquet(path)` | `adapter.read_parquet(path)` |
| `df[df['x'] > 10]` | `WHERE x > 10` |
| `df[['a', 'b']]` | `SELECT a, b` |
| `df.groupby('x')['y'].sum()` | `GROUP BY x, SUM(y)` |
| `df.sort_values('x', ascending=False)` | `ORDER BY x DESC` |
| `df.head(10)` | `LIMIT 10` |

---

## ✅ Checklist de Migração

Ao migrar um arquivo:

- [ ] Substituir `import polars as pl` → `from ... import get_duckdb_adapter`
- [ ] Substituir `import pandas as pd` → `from ... import get_duckdb_adapter`
- [ ] Converter operações DataFrame → SQL
- [ ] Testar com dados reais
- [ ] Validar performance (deve ser mais rápido)
- [ ] Remover imports antigos

---

## 🆘 Problemas Comuns

### Erro: "File not found"

```python
# DuckDB precisa de path absoluto ou relativo correto
# O adapter resolve automaticamente, mas se der erro:
from pathlib import Path
path = str(Path("data/parquet/admmat.parquet").resolve())
df = adapter.read_parquet(path)
```

### Performance pior que esperado

```python
# Verificar se está usando predicate pushdown
# BOM (pushdown):
adapter.query("SELECT * FROM ... WHERE estoque > 0")

# RUIM (sem pushdown):
df = adapter.read_parquet("...")  # Carrega tudo
df = df[df['estoque'] > 0]  # Filtra em memória
```

### SQL syntax error

```python
# DuckDB usa SQL padrão, mas lembre-se:
# - Strings: aspas simples 'texto'
# - Colunas: aspas duplas "coluna" (opcional)
# - LIKE case-sensitive, use ILIKE para case-insensitive
```

---

## 📚 Referências

- **DuckDB Docs**: https://duckdb.org/docs/
- **Auditoria Completa**: `AUDITORIA_FERRAMENTAS_DADOS.md`
- **Plano de Migração**: `PLANO_MIGRACAO_DUCKDB.md`
- **Código do Adapter**: `backend/app/infrastructure/data/duckdb_enhanced_adapter.py`

---

**Pronto para começar!** 🚀

Qualquer dúvida, consulte os documentos acima ou o código do adapter.
