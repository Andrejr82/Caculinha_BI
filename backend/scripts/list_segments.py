"""
List all segments from admmat.parquet

MIGRATED TO DUCKDB (2025-12-31)
- DuckDB DISTINCT query (instant via metadata)
- Faster than Polars scan for this use case
"""
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter


def list_segments():
    parquet_path = Path("data/parquet/admmat.parquet")

    if not parquet_path.exists():
        print(f"[ERROR] Arquivo não encontrado: {parquet_path}")
        return

    print(f"[INFO] Lendo arquivo: {parquet_path} ...")
    start = time.time()

    # Use DuckDB for instant distinct query
    adapter = get_duckdb_adapter()
    parquet_str = str(parquet_path.resolve()).replace("\\", "/")

    # Get unique segments using SQL DISTINCT
    segments = adapter.connection.execute(f"""
        SELECT DISTINCT NOMESEGMENTO
        FROM read_parquet('{parquet_str}')
        WHERE NOMESEGMENTO IS NOT NULL AND NOMESEGMENTO != ''
        ORDER BY NOMESEGMENTO
    """).fetchall()

    # Extract values from tuples
    segments = [seg[0] for seg in segments]

    end = time.time()

    print("\n[SEGMENTS] SEGMENTOS DISPONÍVEIS NO PARQUET:")
    print("=" * 50)
    for seg in segments:
        print(f"  • {seg}")
    print("=" * 50)
    print(f"\n[PERFORMANCE] Tempo de leitura: {(end - start):.4f} segundos")
    print(f"[INFO] Use estes nomes EXATOS ao cadastrar usuários.")


if __name__ == "__main__":
    list_segments()
