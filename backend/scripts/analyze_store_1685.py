import sys
from pathlib import Path
import duckdb
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_store_1685():
    file_path = Path(__file__).parent.parent / "data" / "parquet" / "admmat.parquet"
    # Use as_posix() to avoid backslash issues
    parquet_str = file_path.resolve().as_posix()

    print(f"Analyzing data for Store 1685 from: {parquet_str}")

    query = f"""
    SELECT 
        UNE as LOJA,
        PRODUTO,
        NOME,
        NOMECATEGORIA as CATEGORIA,
        TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE) as PRECO_VENDA,
        TRY_CAST(NULLIF(ULTIMA_ENTRADA_CUSTO_CD, '') AS DOUBLE) as PRECO_CUSTO,
        VENDA_30DD,
        TRY_CAST(NULLIF(ESTOQUE_UNE, '') AS DOUBLE) as ESTOQUE_UNE,
        
        (COALESCE(TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE), 0) - COALESCE(TRY_CAST(NULLIF(ULTIMA_ENTRADA_CUSTO_CD, '') AS DOUBLE), 0)) as MARGEM_VALOR,
        
        CASE 
            WHEN TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE) IS NULL OR TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE) = 0 THEN 0 
            ELSE ((COALESCE(TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE), 0) - COALESCE(TRY_CAST(NULLIF(ULTIMA_ENTRADA_CUSTO_CD, '') AS DOUBLE), 0)) / TRY_CAST(NULLIF(LIQUIDO_38, '') AS DOUBLE)) * 100 
        END as MARGEM_PERCENTUAL
    FROM read_parquet('{parquet_str}')
    WHERE UNE = 1685
    """
    
    try:
        con = duckdb.connect()
        df = con.execute(query).fetchdf()
        
        if df.empty:
            print("No data found for Store 1685.")
            # Let's check which stores exist
            stores = con.execute(f"SELECT DISTINCT UNE FROM read_parquet('{parquet_str}')").fetchdf()
            print(f"Available Stores: {stores['UNE'].tolist()}")
            return

        print(f"\nFound {len(df)} records for Store 1685.")
        
        # Fill NaNs for display
        df = df.fillna(0)

        # 1. Products with Low Sales and High Stock (Capital Parado)
        # Criteria: Sales 30DD < 2 AND Stock > 10
        capital_parado = df[(df['VENDA_30DD'] < 2) & (df['ESTOQUE_UNE'] > 10)].sort_values('ESTOQUE_UNE', ascending=False)
        
        print("\n--- TOP 5 PRODUTOS COM BAIXA VENDA E ALTO ESTOQUE (Capital Parado) ---")
        print(capital_parado[['PRODUTO', 'NOME', 'VENDA_30DD', 'ESTOQUE_UNE', 'PRECO_VENDA']].head(5).to_string(index=False))

        # 2. Products with Negative or Low Margin (< 10%)
        # Filter out zero price/cost artifacts where price is 0 (already handled in calc, but filtering helps)
        low_margin = df[(df['MARGEM_PERCENTUAL'] < 10) & (df['PRECO_VENDA'] > 0)].sort_values('MARGEM_PERCENTUAL', ascending=True)
        
        print("\n--- TOP 5 PRODUTOS COM MARGEM BAIXA OU NEGATIVA ---")
        if low_margin.empty:
            print("Nenhum produto com margem crítica encontrada.")
        else:
            print(low_margin[['PRODUTO', 'NOME', 'PRECO_VENDA', 'PRECO_CUSTO', 'MARGEM_PERCENTUAL']].head(5).to_string(index=False))

        # 3. Categories with Low Performance (Avg Margin)
        # Only consider categories with at least 5 products to avoid noise
        cat_counts = df['CATEGORIA'].value_counts()
        valid_cats = cat_counts[cat_counts >= 5].index
        
        cat_perf = df[df['CATEGORIA'].isin(valid_cats)].groupby('CATEGORIA')['MARGEM_PERCENTUAL'].mean().sort_values().head(5)
        print("\n--- TOP 5 CATEGORIAS COM MENOR MARGEM MÉDIA (Min 5 produtos) ---")
        print(cat_perf.to_string())

        # 4. Total Stock Value
        total_stock_value = (df['ESTOQUE_UNE'] * df['PRECO_CUSTO']).sum()
        print(f"\nValor Total do Estoque (Custo): R$ {total_stock_value:,.2f}")

        # 5. Potential Lost Sales (Stockouts on items with recent sales history - Proxy)
        # Assuming if Sales 30DD > 5 but Stock = 0
        ruptura = df[(df['VENDA_30DD'] > 5) & (df['ESTOQUE_UNE'] == 0)].sort_values('VENDA_30DD', ascending=False)
        print("\n--- TOP 5 RUPTURAS CRÍTICAS (Venda > 5 e Estoque = 0) ---")
        if ruptura.empty:
            print("Nenhuma ruptura crítica encontrada com este critério.")
        else:
            print(ruptura[['PRODUTO', 'NOME', 'VENDA_30DD', 'ESTOQUE_UNE']].head(5).to_string(index=False))

    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_store_1685()
