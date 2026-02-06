"""
Inspect Parquet Schema

MIGRATED TO DUCKDB (2025-12-31)
- Leitura mais rápida de schema
- Sem necessidade de carregar dados na memória
- Usa DuckDB DESCRIBE
"""
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

# Use relative path from project root
file_path = Path(__file__).parent.parent / "data" / "parquet" / "admmat.parquet"

try:
    with open("parquet_schema.txt", "w", encoding="utf-8") as f:
        # Get DuckDB adapter
        adapter = get_duckdb_adapter()
        parquet_str = str(file_path.resolve()).replace("\\", "/")

        # Read schema using DuckDB DESCRIBE
        f.write(f"Schema for {file_path}:\n")
        f.write("=" * 80 + "\n\n")

        schema = adapter.connection.execute(f"""
            SELECT column_name, column_type, null as nullable
            FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_str}'))
        """).fetchall()

        f.write("Columns and Types:\n")
        f.write("-" * 80 + "\n")
        for col_name, col_type, _ in schema:
            f.write(f"{col_name:40s} | {col_type}\n")

        f.write("\n\n")

        # Read first 5 rows using DuckDB
        f.write("First 5 rows:\n")
        f.write("=" * 80 + "\n")

        rows = adapter.connection.execute(f"""
            SELECT * FROM read_parquet('{parquet_str}')
            LIMIT 5
        """).fetchdf()

        f.write(rows.to_string())
        f.write("\n\n")

        # Summary statistics
        total_rows = adapter.connection.execute(f"""
            SELECT COUNT(*) FROM read_parquet('{parquet_str}')
        """).fetchone()[0]

        f.write("\nSummary:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Columns: {len(schema)}\n")
        f.write(f"Total Rows: {total_rows:,}\n")

    print("[OK] Schema saved to parquet_schema.txt")
    print(f"[INFO] Analyzed {len(schema)} columns and {total_rows:,} rows")

except Exception as e:
    print(f"[ERROR] Error reading parquet: {e}")
    import traceback
    traceback.print_exc()
