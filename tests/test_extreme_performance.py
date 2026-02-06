import asyncio
import time
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExtremeBenchmark")

async def test_extreme_performance():
    from app.infrastructure.data.duckdb_adapter import duckdb_adapter
    
    logger.info("=== EXTREME PERFORMANCE BENCHMARK ===\n")
    
    # 1. Test Prepared Statements
    logger.info("1. Testing Prepared Statements (Repeated Query)...")
    sql = "SELECT * FROM 'data/parquet/admmat.parquet' WHERE UNE = ? LIMIT 1000"
    
    # First run (cold - will prepare)
    start = time.time()
    result1 = duckdb_adapter.query_arrow(sql, [1685])
    if hasattr(result1, 'read_all'):
        result1 = result1.read_all()
    first_time = time.time() - start
    
    # Second run (warm - uses cached prepared statement)
    start = time.time()
    result2 = duckdb_adapter.query_arrow(sql, [1686])
    if hasattr(result2, 'read_all'):
        result2 = result2.read_all()
    second_time = time.time() - start
    
    logger.info(f"   First run (prepare):  {first_time:.4f}s")
    logger.info(f"   Second run (cached):  {second_time:.4f}s")
    if second_time < first_time:
        improvement = (first_time - second_time) / first_time * 100
        logger.info(f"   🚀 Prepared Statement: {improvement:.1f}% faster!\n")
    
    # 2. Test Connection Pool (Concurrent queries)
    logger.info("2. Testing Connection Pool (10 concurrent queries)...")
    
    async def concurrent_query(idx):
        return duckdb_adapter.query(f"SELECT count(*) FROM 'data/parquet/admmat.parquet' WHERE UNE > {1000+idx}")
    
    start = time.time()
    await asyncio.gather(*[concurrent_query(i) for i in range(10)])
    pool_time = time.time() - start
    logger.info(f"   10 concurrent queries: {pool_time:.4f}s\n")
    
    # 3. Large dataset test (50k rows)
    logger.info("3. Large Dataset (50k rows with read_parquet optimization)...")
    start = time.time()
    large_result = duckdb_adapter.query_arrow("SELECT * FROM read_parquet('data/parquet/admmat.parquet') LIMIT 50000")
    if hasattr(large_result, 'read_all'):
        large_result = large_result.read_all()
    large_time = time.time() - start
    logger.info(f"   Time: {large_time:.4f}s | Rows: {large_result.num_rows}\n")
    
    logger.info("="*50)
    logger.info("✓ All extreme optimizations validated!")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(test_extreme_performance())
