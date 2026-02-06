import duckdb
try:
    cols = duckdb.sql("SELECT * FROM 'C:/Agente_BI/BI_Solution/data/parquet/admmat.parquet' LIMIT 1").df().columns.tolist()
    print("--- START COLUMNS ---")
    for c in cols:
        print(c)
    print("--- END COLUMNS ---")
except Exception as e:
    print(f"ERROR: {e}")
