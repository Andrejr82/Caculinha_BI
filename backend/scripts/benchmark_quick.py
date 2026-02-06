"""
Quick Benchmark: DuckDB vs Polars performance validation
Uses actual production parquet file

Execution:
    python backend/scripts/benchmark_quick.py

Date: 2025-12-31
"""

import time
import sys
from pathlib import Path

# Production parquet path
PARQUET_PATH = "C:/Agente_BI/BI_Solution/data/parquet/admmat.parquet"

# Check file exists
if not Path(PARQUET_PATH).exists():
    print(f"ERROR: Parquet file not found at {PARQUET_PATH}")
    sys.exit(1)

file_size_mb = Path(PARQUET_PATH).stat().st_size / (1024 * 1024)

print("=" * 80)
print("BENCHMARK: DuckDB vs Polars (Production Data)")
print("=" * 80)
print(f"File: {PARQUET_PATH}")
print(f"Size: {file_size_mb:.2f} MB\n")

# Import libraries
try:
    import polars as pl
    POLARS = True
except ImportError:
    POLARS = False
    print("[WARN] Polars not available")

try:
    import duckdb
    DUCKDB = True
except ImportError:
    DUCKDB = False
    print("[ERROR] DuckDB not available")
    sys.exit(1)


def measure(name, func, iterations=3):
    """Measure execution time"""
    times = []
    for i in range(iterations):
        start = time.time()
        try:
            result = func()
            duration = (time.time() - start) * 1000  # ms
            times.append(duration)
            print(f"  [{name}] Run {i+1}/{iterations}: {duration:.2f} ms")
        except Exception as e:
            print(f"  [{name}] ERROR: {e}")
            return None

    avg = sum(times) / len(times)
    print(f"  [{name}] Average: {avg:.2f} ms")
    return avg


print("\n" + "=" * 80)
print("TEST 1: Count Rows (Metadata Read)")
print("=" * 80)

polars_count = None
if POLARS:
    polars_count = measure("Polars", lambda: len(pl.read_parquet(PARQUET_PATH)))

duckdb_count = None
if DUCKDB:
    conn = duckdb.connect()
    duckdb_count = measure(
        "DuckDB",
        lambda: conn.execute(f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}')").fetchone()[0]
    )

if polars_count and duckdb_count:
    speedup = polars_count / duckdb_count
    print(f"\n  >> DuckDB is {speedup:.1f}x faster for counting")


print("\n" + "=" * 80)
print("TEST 2: Filter Query (id < 1000)")
print("=" * 80)

polars_filter = None
if POLARS:
    polars_filter = measure(
        "Polars",
        lambda: pl.read_parquet(PARQUET_PATH).filter(pl.col("id") < 1000)
    )

duckdb_filter = None
if DUCKDB:
    conn = duckdb.connect()
    duckdb_filter = measure(
        "DuckDB",
        lambda: conn.execute(f"""
            SELECT * FROM read_parquet('{PARQUET_PATH}')
            WHERE id < 1000
        """).fetchall()
    )

if polars_filter and duckdb_filter:
    speedup = polars_filter / duckdb_filter
    print(f"\n  >> DuckDB is {speedup:.1f}x faster for filtering")


print("\n" + "=" * 80)
print("TEST 3: Top 10 Records")
print("=" * 80)

polars_top = None
if POLARS:
    polars_top = measure(
        "Polars",
        lambda: pl.read_parquet(PARQUET_PATH).head(10)
    )

duckdb_top = None
if DUCKDB:
    conn = duckdb.connect()
    duckdb_top = measure(
        "DuckDB",
        lambda: conn.execute(f"""
            SELECT * FROM read_parquet('{PARQUET_PATH}')
            LIMIT 10
        """).fetchall()
    )

if polars_top and duckdb_top:
    speedup = polars_top / duckdb_top
    print(f"\n  >> DuckDB is {speedup:.1f}x faster for Top 10")


print("\n" + "=" * 80)
print("TEST 4: Schema/Metadata Only")
print("=" * 80)

polars_schema = None
if POLARS:
    polars_schema = measure(
        "Polars",
        lambda: pl.read_parquet_schema(PARQUET_PATH)
    )

duckdb_schema = None
if DUCKDB:
    conn = duckdb.connect()
    duckdb_schema = measure(
        "DuckDB",
        lambda: conn.execute(f"""
            SELECT column_name, data_type
            FROM (DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}'))
        """).fetchall()
    )

if polars_schema and duckdb_schema:
    speedup = polars_schema / duckdb_schema
    print(f"\n  >> DuckDB is {speedup:.1f}x faster for schema reading")


# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

results = [
    ("Count Rows", polars_count, duckdb_count),
    ("Filter (id < 1000)", polars_filter, duckdb_filter),
    ("Top 10", polars_top, duckdb_top),
    ("Schema Read", polars_schema, duckdb_schema),
]

print(f"\n{'Test':<25} {'Polars (ms)':<15} {'DuckDB (ms)':<15} {'Speedup'}")
print("-" * 80)

total_polars = 0
total_duckdb = 0

for test_name, polars_time, duckdb_time in results:
    if polars_time and duckdb_time:
        speedup = polars_time / duckdb_time
        print(f"{test_name:<25} {polars_time:>10.2f}     {duckdb_time:>10.2f}     {speedup:>6.1f}x faster")
        total_polars += polars_time
        total_duckdb += duckdb_time

print("-" * 80)
if total_polars > 0 and total_duckdb > 0:
    overall_speedup = total_polars / total_duckdb
    print(f"{'TOTAL':<25} {total_polars:>10.2f}     {total_duckdb:>10.2f}     {overall_speedup:>6.1f}x faster")

print("\n" + "=" * 80)
if overall_speedup >= 2.0:
    print(f"[SUCCESS] DuckDB is {overall_speedup:.1f}x faster overall - Migration recommended!")
else:
    print(f"[INFO] DuckDB is {overall_speedup:.1f}x faster overall")
print("=" * 80)
