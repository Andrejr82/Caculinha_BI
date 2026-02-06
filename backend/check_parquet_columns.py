import duckdb

conn = duckdb.connect()
result = conn.execute("DESCRIBE SELECT * FROM read_parquet('data/parquet/admmat.parquet')").fetchall()

print("\nColunas do arquivo parquet:")
print("="*60)
for col in result[:15]:
    print(f"{col[0]:<30} {col[1]}")
print("="*60)
print(f"\nTotal de colunas: {len(result)}")
