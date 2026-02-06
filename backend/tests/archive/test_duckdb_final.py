"""
Teste direto do DuckDB Enhanced Adapter
Foca apenas na correcao do RecordBatchReader
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("=== TESTE: DuckDB Enhanced Adapter - Correcao RecordBatchReader ===\n")

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

adapter = get_duckdb_adapter()

# Teste 1: query_arrow
print("[1/3] Testando query_arrow...")
try:
    result = adapter.query_arrow("SELECT 1 as id, 'test' as name")
    print(f"OK - Tipo: {type(result).__name__}")
except Exception as e:
    print(f"ERRO: {e}")
    exit(1)

# Teste 2: query_dict (que chama query_arrow internamente)
print("\n[2/3] Testando query_dict...")
try:
    result = adapter.query_dict("SELECT 1 as id, 'test' as name UNION ALL SELECT 2, 'test2'")
    print(f"OK - Retornou {len(result)} registros")
    print(f"     Dados: {result}")
except Exception as e:
    print(f"ERRO: {e}")
    exit(1)

# Teste 3: Metricas
print("\n[3/3] Testando metricas...")
try:
    metrics = adapter.get_metrics()
    print(f"OK - Total queries: {metrics.get('total_queries', 0)}")
    print(f"     Total rows: {metrics.get('total_rows', 0)}")
except Exception as e:
    print(f"ERRO: {e}")
    exit(1)

print("\n=== TODOS OS TESTES PASSARAM ===")
print("A correcao do RecordBatchReader esta funcionando!")
