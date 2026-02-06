# Consultas SQL - Top 10 Vendas por Categoria

## 📊 Consulta 1: Top 10 Categorias por Valor Total

```sql
-- Top 10 categorias ordenadas por valor total de vendas
SELECT TOP 10
    categoria,
    COUNT(*) as total_vendas,
    SUM(valor_venda) as valor_total,
    AVG(valor_venda) as valor_medio,
    MIN(valor_venda) as menor_venda,
    MAX(valor_venda) as maior_venda
FROM vendas
GROUP BY categoria
ORDER BY valor_total DESC;
```

**Resultado esperado:**
| categoria | total_vendas | valor_total | valor_medio | menor_venda | maior_venda |
|-----------|--------------|-------------|-------------|-------------|-------------|
| Eletrônicos | 1500 | 450000.00 | 300.00 | 50.00 | 5000.00 |
| Roupas | 2300 | 230000.00 | 100.00 | 20.00 | 800.00 |
| ... | ... | ... | ... | ... | ... |

---

## 📊 Consulta 2: Top 10 Produtos por Categoria

```sql
-- Top 10 produtos mais vendidos (por valor) em cada categoria
WITH RankedVendas AS (
    SELECT 
        categoria,
        produto,
        SUM(quantidade) as qtd_vendida,
        SUM(valor_venda) as valor_total,
        ROW_NUMBER() OVER (
            PARTITION BY categoria 
            ORDER BY SUM(valor_venda) DESC
        ) as ranking
    FROM vendas
    GROUP BY categoria, produto
)
SELECT 
    categoria,
    produto,
    qtd_vendida,
    valor_total,
    ranking
FROM RankedVendas
WHERE ranking <= 10
ORDER BY categoria, ranking;
```

**Resultado esperado:**
| categoria | produto | qtd_vendida | valor_total | ranking |
|-----------|---------|-------------|-------------|---------|
| Eletrônicos | iPhone 15 | 300 | 150000.00 | 1 |
| Eletrônicos | Samsung TV | 200 | 120000.00 | 2 |
| ... | ... | ... | ... | ... |
| Roupas | Camiseta Nike | 500 | 25000.00 | 1 |
| ... | ... | ... | ... | ... |

---

## 📊 Consulta 3: Top 10 Produtos Globais

```sql
-- Top 10 produtos mais vendidos (independente de categoria)
SELECT TOP 10
    produto,
    categoria,
    SUM(quantidade) as qtd_vendida,
    SUM(valor_venda) as valor_total,
    AVG(valor_venda) as ticket_medio
FROM vendas
GROUP BY produto, categoria
ORDER BY valor_total DESC;
```

---

## 📊 Consulta 4: Top 10 com Percentual do Total

```sql
-- Top 10 categorias com percentual do total
WITH TotalGeral AS (
    SELECT SUM(valor_venda) as total_geral
    FROM vendas
),
VendasPorCategoria AS (
    SELECT 
        categoria,
        COUNT(*) as total_vendas,
        SUM(valor_venda) as valor_total
    FROM vendas
    GROUP BY categoria
)
SELECT TOP 10
    v.categoria,
    v.total_vendas,
    v.valor_total,
    ROUND((v.valor_total * 100.0 / t.total_geral), 2) as percentual_total
FROM VendasPorCategoria v
CROSS JOIN TotalGeral t
ORDER BY v.valor_total DESC;
```

**Resultado esperado:**
| categoria | total_vendas | valor_total | percentual_total |
|-----------|--------------|-------------|------------------|
| Eletrônicos | 1500 | 450000.00 | 35.50% |
| Roupas | 2300 | 230000.00 | 18.15% |
| ... | ... | ... | ... |

---

## 📊 Consulta 5: Top 10 por Período

```sql
-- Top 10 categorias dos últimos 30 dias
SELECT TOP 10
    categoria,
    COUNT(*) as total_vendas,
    SUM(valor_venda) as valor_total,
    AVG(valor_venda) as valor_medio
FROM vendas
WHERE data_venda >= DATEADD(DAY, -30, GETDATE())
GROUP BY categoria
ORDER BY valor_total DESC;
```

---

## 🔧 Adaptação para Parquet (Polars)

Se você estiver usando Parquet com Polars no backend:

```python
import polars as pl

# Carregar dados
df = pl.read_parquet("vendas.parquet")

# Top 10 categorias
top_categorias = (
    df.group_by("categoria")
    .agg([
        pl.count().alias("total_vendas"),
        pl.sum("valor_venda").alias("valor_total"),
        pl.mean("valor_venda").alias("valor_medio"),
        pl.min("valor_venda").alias("menor_venda"),
        pl.max("valor_venda").alias("maior_venda")
    ])
    .sort("valor_total", descending=True)
    .head(10)
)

# Top 10 produtos por categoria
top_produtos = (
    df.group_by(["categoria", "produto"])
    .agg([
        pl.sum("quantidade").alias("qtd_vendida"),
        pl.sum("valor_venda").alias("valor_total")
    ])
    .with_columns([
        pl.col("valor_total")
        .rank("dense", descending=True)
        .over("categoria")
        .alias("ranking")
    ])
    .filter(pl.col("ranking") <= 10)
    .sort(["categoria", "ranking"])
)
```

---

## 💡 Dicas de Performance

### Para SQL Server
```sql
-- Criar índice para melhorar performance
CREATE INDEX IX_Vendas_Categoria_Valor 
ON vendas(categoria, valor_venda DESC);

-- Incluir colunas frequentemente consultadas
CREATE INDEX IX_Vendas_Categoria_Produto 
ON vendas(categoria, produto)
INCLUDE (quantidade, valor_venda, data_venda);
```

### Para Parquet
- Use particionamento por categoria ou data
- Mantenha arquivos entre 100MB-1GB
- Use compressão snappy ou zstd

---

## 📝 Notas

- Ajuste os nomes das colunas (`categoria`, `produto`, `valor_venda`, etc.) conforme seu schema
- Para SQL Server, use `TOP 10`
- Para PostgreSQL, use `LIMIT 10`
- Para MySQL, use `LIMIT 10`
- Para Polars/Parquet, use `.head(10)`
