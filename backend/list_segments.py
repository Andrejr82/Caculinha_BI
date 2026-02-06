"""
Diagnóstico de Segmentos no Parquet
Lista todos os segmentos únicos para verificação de grafia/formatação.
"""
import duckdb
import pandas as pd

def list_segments():
    print("=== DIAGNOSTICO DE SEGMENTOS ===\n")
    try:
        conn = duckdb.connect()
        # Ler segmentos distintos e contar registros
        query = """
        SELECT 
            NOMESEGMENTO, 
            COUNT(*) as qtd_registros,
            SUM(TRY_CAST(VENDA_30DD AS DOUBLE)) as total_vendas
        FROM read_parquet('data/parquet/admmat.parquet')
        GROUP BY NOMESEGMENTO
        ORDER BY qtd_registros DESC
        """
        df = conn.execute(query).df()
        
        print(f"Total de Segmentos encontrados: {len(df)}")
        print("\nTOP 20 SEGMENTOS (Nome | Qtd Registros | Vendas):")
        print("-" * 60)
        for index, row in df.iterrows():
            print(f"'{row['NOMESEGMENTO']}' | {row['qtd_registros']} | R$ {row['total_vendas']:,.2f}")
            
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    list_segments()
