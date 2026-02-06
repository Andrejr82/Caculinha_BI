import duckdb
try:
    cols = duckdb.sql("SELECT * FROM 'C:/Agente_BI/BI_Solution/data/parquet/admmat.parquet' LIMIT 1").df().columns.tolist()
    with open("columns_list.txt", "w", encoding="utf-8") as f:
        for c in cols:
            f.write(c + "\n")
    print("DONE_WRITING_COLUMNS")
except Exception as e:
    print(f"ERROR: {e}")
