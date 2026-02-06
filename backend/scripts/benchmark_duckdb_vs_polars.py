"""
Benchmark: DuckDB vs Polars vs Pandas
Valida performance antes de migração completa

Execução:
    python backend/scripts/benchmark_duckdb_vs_polars.py

Autor: Claude Code
Data: 2025-12-31
"""

import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    print("[WARN] Polars not available")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARN] Pandas not available")

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print("[ERROR] DuckDB not available!")
    sys.exit(1)


class Benchmark:
    def __init__(self, parquet_path: str):
        self.parquet_path = parquet_path
        self.results = {}

    def run_all(self):
        """Run all benchmarks"""
        print("=" * 80)
        print("BENCHMARK: DuckDB vs Polars vs Pandas")
        print("=" * 80)
        print(f"\nParquet file: {self.parquet_path}")

        # Get file size
        file_size_mb = Path(self.parquet_path).stat().st_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB\n")

        tests = [
            ("Read Full", self.test_read_full),
            ("Filter 10%", self.test_filter),
            ("Group By", self.test_groupby),
            ("Top 10", self.test_top_n),
            ("Count Rows", self.test_count),
        ]

        for test_name, test_func in tests:
            print(f"\n{'='*80}")
            print(f"TEST: {test_name}")
            print('='*80)
            test_func()

        self.print_summary()

    def measure(self, func, name: str, iterations: int = 3):
        """Measure execution time"""
        times = []
        for i in range(iterations):
            start = time.time()
            try:
                result = func()
                duration = time.time() - start
                times.append(duration)
                print(f"  [{name}] Iteration {i+1}/{iterations}: {duration*1000:.2f} ms")
            except Exception as e:
                print(f"  [{name}] ERROR: {e}")
                return None

        avg_time = sum(times) / len(times)
        self.results[name] = avg_time
        print(f"  [{name}] Average: {avg_time*1000:.2f} ms")
        return avg_time

    # ========================================
    # Tests
    # ========================================

    def test_read_full(self):
        """Test: Read entire file"""
        if POLARS_AVAILABLE:
            self.measure(
                lambda: pl.read_parquet(self.parquet_path),
                "Polars"
            )

        if PANDAS_AVAILABLE:
            self.measure(
                lambda: pd.read_parquet(self.parquet_path),
                "Pandas"
            )

        if DUCKDB_AVAILABLE:
            conn = duckdb.connect()
            # Use fetchall() instead of df() to avoid Pandas object dtype issues
            self.measure(
                lambda: conn.execute(f"SELECT * FROM read_parquet('{self.parquet_path}')").fetchall(),
                "DuckDB"
            )

    def test_filter(self):
        """Test: Filter 10% of data"""
        filter_col = "id"  # Ajustar conforme schema

        if POLARS_AVAILABLE:
            self.measure(
                lambda: pl.read_parquet(self.parquet_path).filter(
                    pl.col(filter_col) < 1000
                ),
                "Polars Filter"
            )

        if PANDAS_AVAILABLE:
            self.measure(
                lambda: pd.read_parquet(self.parquet_path).query(f"{filter_col} < 1000"),
                "Pandas Filter"
            )

        if DUCKDB_AVAILABLE:
            conn = duckdb.connect()
            self.measure(
                lambda: conn.execute(f"""
                    SELECT * FROM read_parquet('{self.parquet_path}')
                    WHERE {filter_col} < 1000
                """).df(),
                "DuckDB Filter"
            )

    def test_groupby(self):
        """Test: Group by and aggregate"""
        group_col = "UNE"  # Column names are uppercase in parquet
        agg_col = "VENDA_30DD"  # Numeric column for aggregation

        if POLARS_AVAILABLE:
            self.measure(
                lambda: pl.read_parquet(self.parquet_path).group_by(group_col).agg(
                    pl.col(agg_col).sum()
                ),
                "Polars GroupBy"
            )

        if PANDAS_AVAILABLE:
            self.measure(
                lambda: pd.read_parquet(self.parquet_path).groupby(group_col)[agg_col].sum(),
                "Pandas GroupBy"
            )

        if DUCKDB_AVAILABLE:
            conn = duckdb.connect()
            self.measure(
                lambda: conn.execute(f"""
                    SELECT {group_col}, SUM({agg_col}) as total
                    FROM read_parquet('{self.parquet_path}')
                    GROUP BY {group_col}
                """).df(),
                "DuckDB GroupBy"
            )

    def test_top_n(self):
        """Test: Top 10 rows"""
        if POLARS_AVAILABLE:
            self.measure(
                lambda: pl.read_parquet(self.parquet_path).head(10),
                "Polars Top10"
            )

        if PANDAS_AVAILABLE:
            self.measure(
                lambda: pd.read_parquet(self.parquet_path).head(10),
                "Pandas Top10"
            )

        if DUCKDB_AVAILABLE:
            conn = duckdb.connect()
            self.measure(
                lambda: conn.execute(f"""
                    SELECT * FROM read_parquet('{self.parquet_path}')
                    LIMIT 10
                """).df(),
                "DuckDB Top10"
            )

    def test_count(self):
        """Test: Count rows"""
        if POLARS_AVAILABLE:
            self.measure(
                lambda: len(pl.read_parquet(self.parquet_path)),
                "Polars Count"
            )

        if PANDAS_AVAILABLE:
            self.measure(
                lambda: len(pd.read_parquet(self.parquet_path)),
                "Pandas Count"
            )

        if DUCKDB_AVAILABLE:
            conn = duckdb.connect()
            self.measure(
                lambda: conn.execute(f"""
                    SELECT COUNT(*) FROM read_parquet('{self.parquet_path}')
                """).fetchone()[0],
                "DuckDB Count"
            )

    # ========================================
    # Results
    # ========================================

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        # Group by operation
        operations = {}
        for key in self.results:
            op = key.split()[-1]  # Get operation name
            if op not in operations:
                operations[op] = {}
            tool = key.replace(f" {op}", "")
            operations[op][tool] = self.results[key]

        # Print comparison table
        print(f"\n{'Operation':<20} {'Polars':<12} {'Pandas':<12} {'DuckDB':<12} {'Winner'}")
        print("-" * 80)

        for op, tools in operations.items():
            row = f"{op:<20}"
            times = []
            names = []

            for tool_name in ['Polars', 'Pandas', 'DuckDB']:
                if tool_name in tools:
                    time_ms = tools[tool_name] * 1000
                    row += f"{time_ms:>10.2f}ms"
                    times.append(time_ms)
                    names.append(tool_name)
                else:
                    row += f"{'N/A':>12}"

            # Determine winner
            if times:
                winner_idx = times.index(min(times))
                winner = names[winner_idx]
                speedup = max(times) / min(times)
                row += f"  {winner} ({speedup:.1f}x faster)"

            print(row)

        # Calculate overall winner
        duckdb_total = sum(t for k, t in self.results.items() if 'DuckDB' in k)
        polars_total = sum(t for k, t in self.results.items() if 'Polars' in k)
        pandas_total = sum(t for k, t in self.results.items() if 'Pandas' in k)

        print("\n" + "=" * 80)
        print("OVERALL PERFORMANCE")
        print("=" * 80)
        print(f"DuckDB Total: {duckdb_total*1000:.2f} ms")
        print(f"Polars Total: {polars_total*1000:.2f} ms")
        print(f"Pandas Total: {pandas_total*1000:.2f} ms")

        if duckdb_total < polars_total:
            speedup = polars_total / duckdb_total
            print(f"\n[WINNER] DuckDB is {speedup:.2f}x faster than Polars overall")
        else:
            speedup = duckdb_total / polars_total
            print(f"\n[WARNING] Polars is {speedup:.2f}x faster than DuckDB overall")


if __name__ == "__main__":
    # Find parquet file
    parquet_paths = [
        "data/parquet/admmat.parquet",
        "backend/data/parquet/admmat.parquet",
        "/app/app/data/parquet/admmat.parquet",  # Docker path
    ]

    parquet_path = None
    for path in parquet_paths:
        if Path(path).exists():
            parquet_path = str(Path(path).resolve())
            break

    if not parquet_path:
        print("ERROR: Parquet file not found!")
        print("Tried paths:")
        for path in parquet_paths:
            print(f"  - {path}")
        sys.exit(1)

    # Run benchmarks
    benchmark = Benchmark(parquet_path)
    benchmark.run_all()
