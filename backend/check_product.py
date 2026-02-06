import duckdb
con = duckdb.connect()
df = con.execute("SELECT PRODUTO, NOME, VENDA_30DD FROM read_parquet('data/parquet/admmat.parquet') WHERE PRODUTO = '59294' LIMIT 5").fetchdf()
print(df)
print(f"\nTotal: {len(df)} registros")
con.close()
