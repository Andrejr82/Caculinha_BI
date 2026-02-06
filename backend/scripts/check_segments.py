"""
Script para verificar segmentos disponíveis no parquet
"""
import duckdb
from pathlib import Path

# Path para o parquet
project_root = Path(__file__).resolve().parent.parent
parquet_path = project_root / "data" / "parquet" / "admmat.parquet"

print(f"Lendo parquet: {parquet_path}")

# Conectar ao DuckDB
conn = duckdb.connect(database=':memory:')

# Query para listar segmentos únicos
query = f"""
SELECT DISTINCT NOMESEGMENTO
FROM read_parquet('{parquet_path}')
WHERE NOMESEGMENTO IS NOT NULL
ORDER BY NOMESEGMENTO
LIMIT 50
"""

result = conn.execute(query).fetchall()

print("\n=== SEGMENTOS DISPONÍVEIS ===")
for row in result:
    print(f"  - {row[0]}")

# Verificar se Oxford existe
query_oxford = f"""
SELECT COUNT(*) as total, 
       SUM(TRY_CAST(VENDA_30DD AS DOUBLE)) as vendas_total
FROM read_parquet('{parquet_path}')
WHERE UPPER(NOMESEGMENTO) LIKE '%OXFORD%' 
   OR UPPER(NOME) LIKE '%OXFORD%'
   OR UPPER(FABRICANTE) LIKE '%OXFORD%'
"""

result_oxford = conn.execute(query_oxford).fetchone()
print(f"\n=== DADOS OXFORD ===")
print(f"Total de registros: {result_oxford[0]}")
print(f"Vendas totais: R$ {result_oxford[1]:,.2f}" if result_oxford[1] else "Sem vendas")

# Verificar coluna FABRICANTE
query_fabricantes = f"""
SELECT DISTINCT FABRICANTE
FROM read_parquet('{parquet_path}')
WHERE UPPER(FABRICANTE) LIKE '%OXFORD%'
LIMIT 10
"""

result_fab = conn.execute(query_fabricantes).fetchall()
print(f"\n=== FABRICANTES COM 'OXFORD' ===")
for row in result_fab:
    print(f"  - {row[0]}")

conn.close()
