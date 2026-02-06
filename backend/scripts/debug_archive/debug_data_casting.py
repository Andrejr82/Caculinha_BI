
import duckdb
import os
from pathlib import Path

# Try to find the file
possible_paths = [
    r"D:\Dev\Agente_BI\BI_Solution\backend\data\parquet\admmat.parquet",
    r"D:\Dev\Agente_BI\BI_Solution\data\parquet\admmat.parquet"
]

target_path = None
for p in possible_paths:
    if os.path.exists(p):
        target_path = p
        break

if not target_path:
    print("❌ Parquet file not found!")
    exit(1)

print(f"✅ Using parquet: {target_path}")

con = duckdb.connect()

# Check sample values for critical columns
cols = ["LIQUIDO_38", "VENDA_30DD", "ULTIMA_ENTRADA_CUSTO_CD", "ESTOQUE_UNE"]
print(f"\n🔍 Sampling columns: {cols}")

try:
    # Get raw string values first to see formatting
    query = f"SELECT {', '.join(cols)} FROM read_parquet('{target_path}') LIMIT 5"
    print("\n--- Raw Data Check ---")
    results = con.execute(query).fetchall()
    for row in results:
        print(row)

    # Test casting logic
    print("\n--- Casting Test ---")
    # Simulate the query used in dashboard.py
    # Note: If they are strings with commas, TRY_CAST might return NULL
    test_sql = """
        SELECT 
            TRY_CAST(LIQUIDO_38 AS DOUBLE) as liq_cast,
            TRY_CAST(REPLACE(CAST(LIQUIDO_38 AS VARCHAR), ',', '.') AS DOUBLE) as liq_replace,
            LIQUIDO_38
        FROM read_parquet('""" + target_path.replace("\\", "/") + """') 
        WHERE LIQUIDO_38 IS NOT NULL 
        LIMIT 5
    """
    cast_results = con.execute(test_sql).fetchall()
    for row in cast_results:
        print(f"Direct: {row[0]}, Replace: {row[1]}, Original: {row[2]}")

except Exception as e:
    print(f"❌ Query failed: {e}")
