import duckdb
con = duckdb.connect()
query = """
SELECT DISTINCT NOMESEGMENTO, COUNT(*) as cnt
FROM read_parquet('data/parquet/admmat.parquet')
WHERE NOMESEGMENTO IS NOT NULL
GROUP BY NOMESEGMENTO
LIMIT 10
"""
result = con.execute(query).fetchall()
print("Segmentos encontrados:")
for row in result:
    print(f"  - {row[0]}: {row[1]} registros")
con.close()
