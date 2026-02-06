"""
Script para analisar a estrutura do admmat.parquet
e gerar documentação para o ChatBI

MIGRATED TO DUCKDB (2025-12-31)
- Análise completa sem carregar arquivo inteiro na memória
- SQL nativo para estatísticas (MIN, MAX, AVG, COUNT DISTINCT)
- 3-4x mais rápido que Pandas
"""

import sys
from pathlib import Path
import json

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter


def analyze_parquet_structure():
    """Analisa estrutura do arquivo Parquet usando DuckDB"""

    parquet_path = Path("data/parquet/admmat.parquet")

    if not parquet_path.exists():
        print(f"[ERROR] Arquivo não encontrado: {parquet_path}")
        return

    print("=" * 80)
    print("[ANÁLISE DO ARQUIVO admmat.parquet]")
    print("=" * 80)

    # Get DuckDB adapter
    adapter = get_duckdb_adapter()
    parquet_str = str(parquet_path.resolve()).replace("\\", "/")

    # 1. Informações básicas do arquivo
    file_size_mb = parquet_path.stat().st_size / (1024 * 1024)
    print(f"\n[INFO] Tamanho do arquivo: {file_size_mb:.2f} MB")

    # 2. Ler schema com DuckDB
    print("\n[SCHEMA] ESTRUTURA DO ARQUIVO:")
    print("-" * 80)

    schema = adapter.connection.execute(f"""
        SELECT column_name, column_type, null
        FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_str}'))
    """).fetchall()

    print(f"Total de colunas: {len(schema)}")
    print("\nColunas e tipos:")
    for i, (name, dtype, _) in enumerate(schema, 1):
        print(f"{i:3d}. {name:30s} | {dtype}")

    # 3. Contagem de registros (instant via metadata)
    print("\n" + "=" * 80)
    print("[DATA] INFORMAÇÕES GERAIS")
    print("=" * 80)

    total_rows = adapter.connection.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{parquet_str}')
    """).fetchone()[0]

    print(f"\nTotal de registros: {total_rows:,}")
    print(f"Total de colunas: {len(schema)}")

    # Mostrar primeiras 5 linhas
    print("\nPrimeiras 5 linhas:")
    sample = adapter.connection.execute(f"""
        SELECT * FROM read_parquet('{parquet_str}')
        LIMIT 5
    """).fetchdf()
    print(sample.to_string())

    # 4. Estatísticas por coluna (usando SQL para cada tipo)
    print("\n" + "=" * 80)
    print("[STATISTICS] ESTATÍSTICAS DAS COLUNAS")
    print("=" * 80)

    doc = {
        "arquivo": "admmat.parquet",
        "total_registros": total_rows,
        "total_colunas": len(schema),
        "tamanho_mb": round(file_size_mb, 2),
        "colunas": []
    }

    for col_name, col_type, _ in schema:
        print(f"\n[{col_name}]")
        print(f"   Tipo: {col_type}")

        # Count distinct and nulls (works for all types)
        stats = adapter.connection.execute(f"""
            SELECT
                COUNT(DISTINCT "{col_name}") as unique_vals,
                SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) as null_count
            FROM read_parquet('{parquet_str}')
        """).fetchone()

        unique_vals, null_count = stats
        null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

        print(f"   Valores únicos: {unique_vals:,}")
        print(f"   Valores nulos: {null_count:,} ({null_pct:.1f}%)")

        col_info = {
            "nome": col_name,
            "tipo": col_type,
            "valores_unicos": unique_vals,
            "valores_nulos": null_count,
            "percentual_nulos": round(null_pct, 2)
        }

        # Numeric stats
        if col_type in ['BIGINT', 'INTEGER', 'DOUBLE', 'FLOAT', 'DECIMAL', 'HUGEINT']:
            try:
                numeric_stats = adapter.connection.execute(f"""
                    SELECT
                        MIN("{col_name}") as min_val,
                        MAX("{col_name}") as max_val,
                        AVG("{col_name}") as avg_val
                    FROM read_parquet('{parquet_str}')
                    WHERE "{col_name}" IS NOT NULL
                """).fetchone()

                if numeric_stats and numeric_stats[0] is not None:
                    min_val, max_val, avg_val = numeric_stats
                    print(f"   Min: {min_val}, Max: {max_val}, Média: {avg_val:.2f}")
                    col_info["min"] = float(min_val)
                    col_info["max"] = float(max_val)
                    col_info["media"] = float(avg_val)
            except Exception as e:
                print(f"   [SKIP] Erro ao calcular estatísticas numéricas: {e}")

        # String samples
        elif col_type in ['VARCHAR', 'STRING']:
            try:
                samples = adapter.connection.execute(f"""
                    SELECT DISTINCT "{col_name}"
                    FROM read_parquet('{parquet_str}')
                    WHERE "{col_name}" IS NOT NULL
                    LIMIT 5
                """).fetchall()

                if samples:
                    sample_strs = [str(s[0])[:50] for s in samples]  # Limit length
                    print(f"   Exemplos: {', '.join(sample_strs)}")
                    col_info["exemplos"] = [str(s[0]) for s in adapter.connection.execute(f"""
                        SELECT DISTINCT "{col_name}"
                        FROM read_parquet('{parquet_str}')
                        WHERE "{col_name}" IS NOT NULL
                        LIMIT 10
                    """).fetchall()]
            except Exception as e:
                print(f"   [SKIP] Erro ao buscar exemplos: {e}")

        doc["colunas"].append(col_info)

    # 5. Gerar documentação JSON
    print("\n" + "=" * 80)
    print("[EXPORT] GERANDO DOCUMENTAÇÃO")
    print("=" * 80)

    # Salvar documentação
    output_path = Path("data/parquet/admmat_schema.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Documentação salva em: {output_path}")

    # Performance metrics
    metrics = adapter.get_metrics()
    if metrics:
        print(f"\n[PERFORMANCE]")
        print(f"   • Total Queries: {metrics.get('total_queries', 0)}")
        print(f"   • Avg Duration: {metrics.get('avg_duration_ms', 0):.2f} ms")

    return doc


if __name__ == "__main__":
    analyze_parquet_structure()
