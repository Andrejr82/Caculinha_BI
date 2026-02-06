import duckdb
import pandas as pd
from pathlib import Path

parquet_path = Path("D:/Dev/Agente_BI/BI_Solution/data/parquet/admmat.parquet")

try:
    con = duckdb.connect()
    # Listar todas as colunas
    cols = con.execute(f"SELECT * FROM '{parquet_path}' LIMIT 1").df().columns.tolist()
    print("COLUNAS DISPONÍVEIS:")
    for c in sorted(cols):
        print(f"- {c}")
        
    # Verificar colunas suspeitas para fornecedores
    for candidate in ['FORNECEDOR', 'NOME_FORNECEDOR', 'NOMESEGMENTO', 'SEGMENTO', 'FABRICANTE']:
        if candidate in cols:
            print(f"\nVerificando dados em {candidate}:")
            sample = con.execute(f"SELECT {candidate}, COUNT(*) as n FROM '{parquet_path}' GROUP BY {candidate} LIMIT 5").fetchall()
            print(sample)

except Exception as e:
    print(f"Erro: {e}")
