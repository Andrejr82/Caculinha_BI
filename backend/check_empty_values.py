"""
Check for empty string values in numeric columns
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import duckdb

# Path to parquet file
parquet_path = Path(__file__).parent / "data" / "parquet" / "admmat.parquet"
parquet_str = str(parquet_path.resolve()).replace("\\", "/")

print(f"Checking: {parquet_str}\n")

conn = duckdb.connect(database=':memory:')

# Get schema
print("=== SCHEMA ===")
schema = conn.execute(f"""
    SELECT column_name, column_type
    FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_str}'))
""").fetchall()

for col_name, col_type in schema:
    print(f"{col_name:40s} | {col_type}")

print("\n=== CHECKING FOR EMPTY STRINGS IN KEY COLUMNS ===\n")

# Check for empty strings in numeric columns
numeric_cols = ['VENDA_30DD', 'ESTOQUE_UNE', 'ESTOQUE_CD', 'PRECO_VENDA', 'PRECO_CUSTO', 'MES_01']

for col in numeric_cols:
    # Check if column exists
    col_exists = any(col_name == col for col_name, _ in schema)
    if not col_exists:
        print(f"[SKIP] {col} - column does not exist")
        continue

    # Check for empty strings
    try:
        empty_count = conn.execute(f"""
            SELECT COUNT(*)
            FROM read_parquet('{parquet_str}')
            WHERE "{col}" = ''
        """).fetchone()[0]

        # Check for NULL values
        null_count = conn.execute(f"""
            SELECT COUNT(*)
            FROM read_parquet('{parquet_str}')
            WHERE "{col}" IS NULL
        """).fetchone()[0]

        # Total rows
        total_rows = conn.execute(f"""
            SELECT COUNT(*)
            FROM read_parquet('{parquet_str}')
        """).fetchone()[0]

        # Sample values
        samples = conn.execute(f"""
            SELECT DISTINCT "{col}"
            FROM read_parquet('{parquet_str}')
            LIMIT 10
        """).fetchall()

        print(f"{col}:")
        print(f"  Total rows: {total_rows:,}")
        print(f"  Empty strings: {empty_count:,}")
        print(f"  NULL values: {null_count:,}")
        print(f"  Sample values: {[s[0] for s in samples[:5]]}")

        if empty_count > 0:
            print(f"  ⚠️  PROBLEM: {empty_count:,} empty strings found!")
        print()

    except Exception as e:
        print(f"[ERROR] {col}: {e}\n")

print("\n=== TESTING CAST OPERATIONS ===\n")

# Test the exact CAST operations used in analytics.py
test_cols = [
    ('VENDA_30DD', 'DOUBLE'),
    ('ESTOQUE_UNE', 'DOUBLE'),
    ('MES_01', 'DOUBLE')
]

for col, cast_type in test_cols:
    col_exists = any(col_name == col for col_name, _ in schema)
    if not col_exists:
        print(f"[SKIP] {col} - column does not exist")
        continue

    try:
        result = conn.execute(f"""
            SELECT CAST("{col}" AS {cast_type}) as value
            FROM read_parquet('{parquet_str}')
            WHERE "{col}" IS NOT NULL AND "{col}" != ''
            LIMIT 5
        """).fetchall()
        print(f"✓ CAST({col} AS {cast_type}) - OK")
        print(f"  Sample values: {[r[0] for r in result]}")
    except Exception as e:
        print(f"✗ CAST({col} AS {cast_type}) - FAILED")
        print(f"  Error: {e}")
    print()

conn.close()
print("\n[DONE] Check complete")
