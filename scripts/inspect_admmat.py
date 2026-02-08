import duckdb
import pandas as pd

parquet_path = r"C:\Projetos_BI\BI_Solution\backend\data\parquet\admmat.parquet"

def inspect_parquet():
    con = duckdb.connect()
    # Get columns using DESCRIBE on a scan
    cols_df = con.query(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").to_df()
    cols = cols_df['column_name'].tolist()
    print(f"Total columns: {len(cols)}")
    
    # Common taxonomy names: DEPARTAMENTO, CATEGORIA, SECAO, GRUPO, SUBGRUPO, DESCRICAO, NOME, MARCA
    search_terms = ['DESC', 'NOME', 'DEP', 'CAT', 'SEC', 'GRP', 'FAM', 'MARCA', 'PROD', 'SKU', 'EAN', 'LINHA']
    target_cols = [c for c in cols if any(x in c.upper() for x in search_terms)]
    print(f"Target columns: {target_cols}")
    
    # Get sample values for these columns
    if target_cols:
        # Avoid too many columns for display
        display_cols = target_cols[:20]
        data = con.query(f"SELECT {', '.join(display_cols)} FROM read_parquet('{parquet_path}') LIMIT 10").to_df()
        print("\n--- SAMPLE METADATA ---")
        print(data.to_string())

if __name__ == "__main__":
    inspect_parquet()
