import duckdb
import pandas as pd
import os

try:
    parquet_path = os.path.join("data", "parquet", "admmat.parquet")
    con = duckdb.connect()
    
    # Check columns first
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}') LIMIT 1").fetchall()
    col_names = [c[0] for c in cols]
    print(f"Columns: {col_names}")
    
    segment_col = next((c for c in ['NOMESEGMENTO', 'SEGMENTO', 'nomesegmento'] if c in col_names), None)
    
    if segment_col:
        query = f"SELECT DISTINCT {segment_col} FROM read_parquet('{parquet_path}') ORDER BY 1"
        segments = con.execute(query).fetchall()
        print("\nSegments:")
        for s in segments:
            print(f"- {s[0]}")
    else:
        print("Segment column not found.")
        
except Exception as e:
    print(f"Error: {e}")
