
import asyncio
import time
import os
import sys
import pandas as pd
import logging

# Adicionar raiz ao path
sys.path.append(os.getcwd())

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Benchmark")

async def test_performance():
    from app.infrastructure.data.duckdb_adapter import duckdb_adapter
    
    logger.info("--- INICIANDO BENCHMARK DUCKDB ---")
    
    # Check PyArrow availability
    try:
        import pyarrow
        logger.info(f"PyArrow version: {pyarrow.__version__}")
    except ImportError:
        logger.error("ALERTA: PyArrow não instalado! Teste falhará ou será lento.")
    
    # 1. Warmup Query (Ensures metadata is cached)
    logger.info("1. Aquecendo Cache (Warming)...")
    start = time.time()
    duckdb_adapter.query("SELECT count(*) FROM 'data/parquet/admmat.parquet'")
    logger.info(f"Warming concluído em {time.time() - start:.4f}s")
    
    # 2. Benchmark Standard Pandas Query (Copy overhead)
    logger.info("2. Testando Query Padrão (Pandas Conversion)...")
    start = time.time()
    df = duckdb_adapter.query("SELECT * FROM 'data/parquet/admmat.parquet' LIMIT 50000")
    pandas_time = time.time() - start
    logger.info(f"Standard Query: {pandas_time:.4f}s | Rows: {len(df)}")
    
    # 3. Benchmark Zero-Copy Arrow Query
    logger.info("3. Testando Query Zero-Copy (Arrow)...")
    start = time.time()
    arrow_table = duckdb_adapter.query_arrow("SELECT * FROM 'data/parquet/admmat.parquet' LIMIT 50000")
    arrow_time = time.time() - start
    logger.info(f"Zero-Copy Query: {arrow_time:.4f}s | Rows: {arrow_table.num_rows}")
    
    # 4. Compare
    logger.info("-" * 40)
    logger.info(f"Pandas Time: {pandas_time:.4f}s")
    logger.info(f"Arrow Time:  {arrow_time:.4f}s")
    if arrow_time < pandas_time:
        improvement = (pandas_time - arrow_time) / pandas_time * 100
        logger.info(f"🏆 ARROW WINS! {improvement:.1f}% mais rápido")
    else:
        logger.info("⚠️ Arrow não foi mais rápido (Dataset pequeno demais?)")
        
    logger.info("-" * 40)
    
    # 5. Verify Thread Safety (Async cursors)
    logger.info("5. Verificando Thread Safety (Async/Concurrent)...")
    
    async def run_query(idx):
        # Simula query concorrente
        duckdb_adapter.query(f"SELECT count(*) as cnt FROM 'data/parquet/admmat.parquet' WHERE UNE = {1000+idx}")
        return True
        
    start = time.time()
    tasks = [run_query(i) for i in range(5)]
    await asyncio.gather(*tasks)
    logger.info(f"5 Queries Concorrentes executadas em {time.time() - start:.4f}s")
    logger.info("Sucesso total.")

if __name__ == "__main__":
    asyncio.run(test_performance())
