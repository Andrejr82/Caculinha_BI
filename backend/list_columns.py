import duckdb
import pandas as pd
from pathlib import Path

parquet_path = Path("D:/Dev/Agente_BI/BI_Solution/data/parquet/admmat.parquet")

try:
    con = duckdb.connect()
    # Listar colunas
    df = con.execute(f"SELECT * FROM '{parquet_path}' LIMIT 1").df()
    print("COLUMNS FOUND:")
    for c in sorted(df.columns):
        print(f"- {c}")

except Exception as e:
    print(f"Erro: {e}")
