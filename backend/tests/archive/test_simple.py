"""
Script de teste simplificado para DuckDB
"""
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("Importando DuckDB adapter...")
from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

print("Obtendo adapter...")
adapter = get_duckdb_adapter()

print("\n=== Teste 1: Query Arrow ===")
try:
    result = adapter.query_arrow("SELECT 1 as id, 'test' as name")
    print(f"✅ Sucesso! Tipo: {type(result)}")
    print(f"   Tem __len__: {hasattr(result, '__len__')}")
    if hasattr(result, '__len__'):
        print(f"   Tamanho: {len(result)}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Teste 2: Query Dict ===")
try:
    result = adapter.query_dict("SELECT 1 as id, 'test' as name")
    print(f"✅ Sucesso! Tipo: {type(result)}")
    print(f"   Dados: {result}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Teste 3: Métricas ===")
try:
    metrics = adapter.get_metrics()
    print(f"✅ Métricas: {metrics}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Testes concluídos!")
