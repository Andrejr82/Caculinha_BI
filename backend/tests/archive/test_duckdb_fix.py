"""
Script de teste para validar a correção do DuckDBEnhancedAdapter
Testa especificamente o erro: object of type 'RecordBatchReader' has no len()
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

def test_query_arrow():
    """Testa query_arrow com diferentes tipos de resultado"""
    print("\n=== Teste 1: query_arrow ===")
    adapter = get_duckdb_adapter()
    
    try:
        # Query simples que retorna Arrow Table
        result = adapter.query_arrow("SELECT 1 as id, 'test' as name")
        print(f"✅ query_arrow executado com sucesso")
        print(f"   Tipo do resultado: {type(result)}")
        print(f"   Linhas: {len(result) if hasattr(result, '__len__') else 'N/A'}")
    except Exception as e:
        print(f"❌ Erro em query_arrow: {e}")
        return False
    
    return True

def test_query_dict():
    """Testa query_dict que chama query_arrow internamente"""
    print("\n=== Teste 2: query_dict ===")
    adapter = get_duckdb_adapter()
    
    try:
        result = adapter.query_dict("SELECT 1 as id, 'test' as name UNION ALL SELECT 2, 'test2'")
        print(f"✅ query_dict executado com sucesso")
        print(f"   Tipo do resultado: {type(result)}")
        print(f"   Registros: {len(result)}")
        print(f"   Dados: {result}")
    except Exception as e:
        print(f"❌ Erro em query_dict: {e}")
        return False
    
    return True

def test_parquet_query():
    """Testa query em arquivo Parquet (se disponível)"""
    print("\n=== Teste 3: Query em Parquet ===")
    adapter = get_duckdb_adapter()
    
    # Tentar encontrar um arquivo parquet
    parquet_paths = [
        "data/parquet/admmat.parquet",
        "backend/data/parquet/admmat.parquet",
        "../data/parquet/admmat.parquet"
    ]
    
    parquet_file = None
    for path in parquet_paths:
        if Path(path).exists():
            parquet_file = path
            break
    
    if not parquet_file:
        print("⚠️  Nenhum arquivo parquet encontrado, pulando teste")
        return True
    
    try:
        sql = f"SELECT * FROM read_parquet('{parquet_file}') LIMIT 5"
        result = adapter.query_dict(sql)
        print(f"✅ Query em parquet executado com sucesso")
        print(f"   Arquivo: {parquet_file}")
        print(f"   Registros retornados: {len(result)}")
    except Exception as e:
        print(f"❌ Erro em query parquet: {e}")
        return False
    
    return True

def test_metrics():
    """Testa se as métricas estão sendo registradas corretamente"""
    print("\n=== Teste 4: Métricas ===")
    adapter = get_duckdb_adapter()
    
    # Resetar métricas
    adapter.reset_metrics()
    
    # Executar algumas queries
    adapter.query_dict("SELECT 1")
    adapter.query_dict("SELECT 2")
    
    metrics = adapter.get_metrics()
    print(f"✅ Métricas coletadas:")
    print(f"   Total de queries: {metrics.get('total_queries', 0)}")
    print(f"   Duração média: {metrics.get('avg_duration_ms', 0):.2f}ms")
    
    return metrics.get('total_queries', 0) >= 2

def main():
    print("=" * 70)
    print("TESTE DE CORREÇÃO: DuckDBEnhancedAdapter")
    print("Objetivo: Validar correção do erro 'RecordBatchReader has no len()'")
    print("=" * 70)
    
    tests = [
        test_query_arrow,
        test_query_dict,
        test_parquet_query,
        test_metrics
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro inesperado em {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total}")
    
    if passed == total:
        print("✅ TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        return 1

if __name__ == "__main__":
    exit(main())
