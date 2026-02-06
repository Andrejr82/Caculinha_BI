import duckdb
from pathlib import Path

# Find parquet
base_path = Path("d:/Dev/Agente_BI/BI_Solution/data/parquet/admmat.parquet")
if not base_path.exists():
    print("Parquet file not found at expected path, trying relative...")
    # fallback logic similar to code
    base_path = Path("backend/data/parquet/admmat.parquet")

print(f"Reading {base_path}")
try:
    con = duckdb.connect()
    # Limit 1 just to see columns
    df = con.execute(f"SELECT * FROM read_parquet('{str(base_path)}') LIMIT 1").fetchdf()
    # print("Columns:", df.columns.tolist())
    
    # Check if UNE_NOME exists
    print("\nALL COLUMNS FOUND:")
    for col in sorted(df.columns):
        print(f"   {col}")
        
    con.close()
except Exception as e:
    print(f"Error: {e}")
