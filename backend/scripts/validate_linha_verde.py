"""
Script para validar LINHA VERDE - Versão 2
Busca registros com valores não nulos para análise.
"""
import duckdb

conn = duckdb.connect()

# Buscar registros com valores de estoque preenchidos
query = """
SELECT 
    PRODUTO,
    UNE,
    ESTOQUE_LV,
    ESTOQUE_GONDOLA_LV,
    ESTOQUE_ILHA_LV,
    ESTOQUE_UNE,
    MEDIA_CONSIDERADA_LV,
    MEDIA_TRAVADA
FROM read_parquet('backend/data/parquet/admmat.parquet')
WHERE TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0
  OR TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE) > 0
LIMIT 20
"""

print("=== DADOS DE ESTOQUE ===")
print()

result = conn.execute(query).fetchdf()
print(result.to_string())

# Verificar se LV = GONDOLA + ILHA (ou se tem outro cálculo)
print("\n=== ANÁLISE DE CÁLCULO ===")

check_query = """
SELECT 
    COUNT(*) as total,
    SUM(CASE 
        WHEN TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0 
         AND TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE) > 0
        THEN 1 ELSE 0 
    END) as LV_e_GONDOLA_preenchidos,
    SUM(CASE 
        WHEN ABS(
            TRY_CAST(ESTOQUE_LV AS DOUBLE) - 
            (COALESCE(TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE), 0) + COALESCE(TRY_CAST(ESTOQUE_ILHA_LV AS DOUBLE), 0))
        ) < 0.01
        THEN 1 ELSE 0
    END) as LV_igual_SOMA
FROM read_parquet('backend/data/parquet/admmat.parquet')
WHERE TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0
"""

result2 = conn.execute(check_query).fetchone()
print(f"Total registros com LV > 0: {result2[0]}")
print(f"LV e GONDOLA preenchidos: {result2[1]}")
print(f"LV = GONDOLA + ILHA (match exato): {result2[2]}")

conn.close()
