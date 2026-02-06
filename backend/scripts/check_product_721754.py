"""Script para investigar produto 721754 - CANECA CRISTAL ECOLOGICO 190ML"""
import duckdb
from pathlib import Path

parquet_path = Path(__file__).parent.parent / "data" / "parquet" / "admmat.parquet"

con = duckdb.connect()

# Consultar dados do produto
query = f"""
SELECT 
    PRODUTO, 
    NOME, 
    NOMESEGMENTO, 
    NOMEGRUPO, 
    VENDA_30DD, 
    ESTOQUE_UNE
FROM read_parquet('{parquet_path}')
WHERE PRODUTO = '721754'
LIMIT 10
"""

result = con.execute(query).fetchall()
columns = ['PRODUTO', 'NOME', 'NOMESEGMENTO', 'NOMEGRUPO', 'VENDA_30DD', 'ESTOQUE_UNE']

print("=" * 80)
print("DADOS DO PRODUTO 721754 - CANECA CRISTAL ECOLOGICO 190ML")
print("=" * 80)

for row in result:
    for col, val in zip(columns, row):
        print(f"{col:20s}: {val}")
    print("-" * 80)

con.close()
