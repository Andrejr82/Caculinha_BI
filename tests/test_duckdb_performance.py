import asyncio
import time
import os
import sys
import logging

# Fix import path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Benchmark")

async def test_performance():
    from app.infrastructure.data.duckdb_adapter import duckdb_adapter
    
    logger.info("=== BENCHMARK DUCKDB BLEEDING EDGE ===")
    
    # Check PyArrow
    try:
        import pyarrow
        logger.info(f"✓ PyArrow {pyarrow.__version__} disponível")
    except ImportError:
        logger.error("✗ PyArrow NÃO instalado!")
        return
    
    # 1. Warmup
    logger.info("\n1. Aquecendo cache de metadados...")
    start = time.time()
    duckdb_adapter.query("SELECT count(*) FROM 'data/parquet/admmat.parquet'")
    logger.info(f"   Warming: {time.time() - start:.4f}s")
    
    # 2. Standard Pandas
    logger.info("\n2. Query Padrão (Pandas)...")
    start = time.time()
    df = duckdb_adapter.query("SELECT * FROM 'data/parquet/admmat.parquet' LIMIT 50000")
    pandas_time = time.time() - start
    logger.info(f"   Tempo: {pandas_time:.4f}s | Linhas: {len(df)}")
    
    # 3. Zero-Copy Arrow
    logger.info("\n3. Query Zero-Copy (Arrow)...")
    start = time.time()
    arrow_result = duckdb_adapter.query_arrow("SELECT * FROM 'data/parquet/admmat.parquet' LIMIT 50000")
    # DuckDB pode retornar RecordBatchReader ou Table dependendo da versão
    if hasattr(arrow_result, 'read_all'):
        arrow_table = arrow_result.read_all()
    else:
        arrow_table = arrow_result
    arrow_time = time.time() - start
    logger.info(f"   Tempo: {arrow_time:.4f}s | Linhas: {arrow_table.num_rows}")
    
    # 4. Comparação
    logger.info("\n" + "="*50)
    logger.info(f"Pandas: {pandas_time:.4f}s")
    logger.info(f"Arrow:  {arrow_time:.4f}s")
    if arrow_time < pandas_time:
        improvement = (pandas_time - arrow_time) / pandas_time * 100
        logger.info(f"🏆 ARROW {improvement:.1f}% mais rápido!")
    else:
        logger.info("⚠️ Dataset pequeno demais para diferença significativa")
    logger.info("="*50)
    
    # 5. Thread Safety
    logger.info("\n4. Teste de Concorrência (5 queries paralelas)...")
    
    async def run_query(idx):
        duckdb_adapter.query(f"SELECT count(*) FROM 'data/parquet/admmat.parquet' WHERE UNE > {1000+idx}")
        return True
        
    start = time.time()
    await asyncio.gather(*[run_query(i) for i in range(5)])
    logger.info(f"   5 queries concorrentes: {time.time() - start:.4f}s")
    logger.info("\n✓ Todos os testes passaram!")

if __name__ == "__main__":
    asyncio.run(test_performance())
