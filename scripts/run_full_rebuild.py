
import asyncio
import structlog
import time
from backend.infrastructure.adapters.source.product_source_parquet_adapter import ProductSourceParquetAdapter
from backend.infrastructure.adapters.repository.duckdb_catalog_repository import DuckDBCatalogRepository
from backend.application.services.catalog_builder_service import CatalogBuilderService
from backend.application.services.pt_br_normalizer import PTBRNormalizer

# Configure logging
structlog.configure()

async def run_rebuild():
    parquet_path = r"C:\Projetos_BI\BI_Solution\backend\data\parquet\admmat.parquet"
    db_path = r"C:\Projetos_BI\BI_Solution\backend\data\product_catalog.duckdb"
    
    # Force clean start
    import os
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            print(f"⚠️ Could not remove {db_path}, it might be locked.")
    
    source = ProductSourceParquetAdapter(parquet_path)
    # DuckDB repository acts as repository, version manager and synonym storage
    repo = DuckDBCatalogRepository(db_path)
    normalizer = PTBRNormalizer()
    
    # We need to wrap normalizer in a class that implements INormalizationPort if needed
    # (The current Normalizer is a class with static methods, but we'll use it directly in the service)
    
    builder = CatalogBuilderService(
        source=source,
        repository=repo,
        version_manager=repo,
        normalizer=normalizer
    )
    
    start_time = time.time()
    print("🚀 Starting Full Catalog Rebuild...")
    version_id = await builder.rebuild_catalog("Initial Test Recovery")
    end_time = time.time()
    
    print(f"✅ Rebuild Completed in {end_time - start_time:.2f} seconds.")
    print(f"📦 Version ID: {version_id}")
    
    # Quick Check
    active = await repo.get_active_version()
    print(f"🔔 Active Version: {active}")
    
    sample_products = await repo.list_products(version_id, limit=5)
    print("\n--- SAMPLE CANONICAL PRODUCTS ---")
    for p in sample_products:
        print(f"ID: {p.product_id} | Name: {p.name_canonical} | Searchable: {p.searchable_text[:50]}...")

if __name__ == "__main__":
    asyncio.run(run_rebuild())
