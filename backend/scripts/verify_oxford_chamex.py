
import duckdb

# Caminho absoluto para garantir execução sem problemas de import
PARQUET_PATH = r"C:\Agente_BI\BI_Solution\backend\data\parquet\admmat.parquet"

def check_oxford_data():
    try:
        conn = duckdb.connect()
        conn.execute(f"CREATE OR REPLACE VIEW vendas AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
        
        # 1. Verificar produtos que contêm "OXFORD" no GRUPO ou NOME
        print("\n--- Produtos com 'OXFORD' no GRUPO ---")
        query_group = """
            SELECT DISTINCT NOMEGRUPO, PRODUTO, NOME, VENDA_30DD 
            FROM vendas 
            WHERE NOMEGRUPO ILIKE '%OXFORD%' 
            ORDER BY VENDA_30DD DESC 
            LIMIT 5
        """
        results_group = conn.execute(query_group).fetchall()
        if not results_group:
            print("Nenhum grupo encontrado com 'OXFORD'")
        for r in results_group:
            print(r)
            
        print("\n--- Produtos com 'OXFORD' no SEGMENTO ---")
        query_seg = """
            SELECT DISTINCT NOMESEGMENTO, PRODUTO, NOME, VENDA_30DD 
            FROM vendas 
            WHERE NOMESEGMENTO ILIKE '%OXFORD%' 
            ORDER BY VENDA_30DD DESC 
            LIMIT 5
        """
        results_seg = conn.execute(query_seg).fetchall()
        if not results_seg:
            print("Nenhum segmento encontrado com 'OXFORD'")
        for r in results_seg:
            print(r)

        # 2. Verificar o que é SKU 59294 (Chamex citado)
        print("\n--- Dados do SKU 59294 (Chamex citado) ---")
        query_sku = """
            SELECT PRODUTO, NOME, NOMEGRUPO, NOMESEGMENTO, VENDA_30DD 
            FROM vendas 
            WHERE PRODUTO = 59294
        """
        result_sku = conn.execute(query_sku).fetchall()
        for r in result_sku:
            print(r)

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_oxford_data()
