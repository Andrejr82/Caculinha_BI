import duckdb
try:
    cols = duckdb.sql("SELECT * FROM 'C:/Agente_BI/BI_Solution/data/parquet/admmat.parquet' LIMIT 1").df().columns.tolist()
    print("COLUMNS_FOUND:", cols)
except Exception as e:
    print(f"ERROR: {e}")
