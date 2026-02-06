import duckdb
import pandas as pd
from pathlib import Path

parquet_path = Path("D:/Dev/Agente_BI/BI_Solution/data/parquet/admmat.parquet")

try:
    con = duckdb.connect()
    
    print(f"Path: {parquet_path}")
    
    # 1. Verificar se NOMESEGMENTO existe e tem dados
    print("\n1. Checando coluna NOMESEGMENTO:")
    res = con.execute(f"SELECT COUNT(*) FROM '{parquet_path}' WHERE NOMESEGMENTO IS NOT NULL").fetchone()
    print(f"Total rows with NOMESEGMENTO: {res[0]}")
    
    # 2. Query exata do endpoint (simplificada)
    print("\n2. Executando query do dashboard:")
    query = f"""
        SELECT 
            NOMESEGMENTO as nome,
            AVG(COALESCE(DIAS_ULTIMA_ENTRADA, 0)) as lead_time_medio,
            COUNT(CASE WHEN ESTOQUE_ATUAL <= 0 THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0) as taxa_ruptura,
            AVG(COALESCE(ULTIMA_ENTRADA_CUSTO_CD, 0)) as custo_medio,
            COUNT(DISTINCT PRODUTO) as produtos_fornecidos,
            MAX(COALESCE(DATA_ULTIMA_ENTRADA, CURRENT_DATE)) as ultima_entrega
        FROM '{parquet_path}'
        WHERE NOMESEGMENTO IS NOT NULL AND TRIM(NOMESEGMENTO) != '' AND NOMESEGMENTO != 'nan'
        GROUP BY NOMESEGMENTO
        ORDER BY taxa_ruptura DESC
        LIMIT 5
    """
    
    results = con.execute(query).fetchall()
    if results:
        print("Sucesso! Resultados encontrados:")
        for r in results:
            print(r)
    else:
        print("Nenhum resultado retornado.")
        
        # Debug: Listar valores únicos de NOMESEGMENTO
        print("\nDebug: Valores únicos de NOMESEGMENTO (Top 10):")
        unique = con.execute(f"SELECT DISTINCT NOMESEGMENTO FROM '{parquet_path}' LIMIT 10").fetchall()
        print(unique)

except Exception as e:
    print(f"Erro: {e}")
