
import duckdb
import os

base_path = r"D:\Dev\Agente_BI\BI_Solution\backend\data\parquet\admmat.parquet"

try:
    if not os.path.exists(base_path):
        print(f"❌ File not found at: {base_path}")
    else:
        print(f"✅ Found file at: {base_path}")
        con = duckdb.connect()
        df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{base_path}') LIMIT 1").fetchdf()
        print("\nColumns found:")
        for col in df['column_name']:
            print(f"- {col}")
except Exception as e:
    print(f"❌ Error: {e}")
