import duckdb
import os
from backend.app.config.settings import get_settings

settings = get_settings()
parquet_path = settings.PARQUET_FILE_PATH

# Adjust path if relative to backend root
if not os.path.exists(parquet_path):
    parquet_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), parquet_path)

if not os.path.exists(parquet_path):
    # Try one level up if run from backend subdir
    parquet_path = os.path.join("..", settings.PARQUET_FILE_PATH)
    
if not os.path.exists(parquet_path):
    print(f"Error: Parquet file not found at {parquet_path}")
else:
    print(f"Inspecting Parquet: {parquet_path}")
    con = duckdb.connect()
    try:
        # Get columns
        columns = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").fetchall()
        print("\nColumns found:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
            
        # Check specifically for U... columns
        print("\nChecking for 'U...' columns:")
        for col in columns:
            if col[0].upper().startswith('U'):
                print(f"  - {col[0]}")
    except Exception as e:
        print(f"Error reading parquet: {e}")
