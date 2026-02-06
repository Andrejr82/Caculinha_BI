import duckdb
import traceback

con = duckdb.connect()
parquet_path = "data/parquet/admmat.parquet"

query = f"""
SELECT 
    NOMESEGMENTO as nome,
    0 as lead_time_medio,
    COUNT(CASE WHEN CAST(ESTOQUE_UNE AS DOUBLE) <= 0 THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0) as taxa_ruptura,
    AVG(COALESCE(CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE), 0)) as custo_medio,
    COUNT(DISTINCT PRODUTO) as produtos_fornecidos,
    MAX(CAST(COALESCE(ULTIMA_ENTRADA_DATA_UNE, '') AS VARCHAR)) as ultima_entrega
FROM read_parquet('{parquet_path}')
WHERE NOMESEGMENTO IS NOT NULL AND TRIM(NOMESEGMENTO) != '' AND NOMESEGMENTO != 'nan'
GROUP BY NOMESEGMENTO
ORDER BY taxa_ruptura DESC
LIMIT 20
"""

try:
    result = con.execute(query).fetchall()
    print(f"Resultados: {len(result)}")
    for row in result[:5]:
        print(row)
except Exception as e:
    print(f"ERRO: {e}")
    traceback.print_exc()
finally:
    con.close()
