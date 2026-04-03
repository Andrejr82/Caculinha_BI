"""
Catalog API Router — Endpoints de Gestão do Catálogo Semântico

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.application.services.catalog_builder_service import CatalogBuilderService
from backend.application.services.product_search_service import ProductSearchService
from backend.infrastructure.adapters.repository.duckdb_catalog_repository import DuckDBCatalogRepository
from backend.infrastructure.adapters.source.product_source_parquet_adapter import ProductSourceParquetAdapter
from backend.application.services.pt_br_normalizer import PTBRNormalizer
from backend.infrastructure.adapters.search.vector_index_adapter import VectorIndexAdapter
from backend.infrastructure.adapters.search.hybrid_ranking_adapter import HybridRankingAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["Semantic Catalog"])

# --- Models ---

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class RebuildRequest(BaseModel):
    description: str = "Manual Rebuild via API"

# --- Dependency Injection (Simplified for MVP) ---

def get_services():
    db_path = "backend/data/product_catalog.duckdb"
    index_dir = "backend/data/whoosh_index"
    parquet_path = "backend/data/parquet/admmat.parquet"

    repo = DuckDBCatalogRepository(db_path)
    source = ProductSourceParquetAdapter(parquet_path)
    normalizer = PTBRNormalizer()

    try:
        from backend.infrastructure.adapters.search.whoosh_bm25_index_adapter import WhooshBM25IndexAdapter

        bm25 = WhooshBM25IndexAdapter(index_dir)
    except Exception as exc:
        logger.exception("Catalog BM25 unavailable; semantic catalog endpoints disabled")
        raise HTTPException(
            status_code=503,
            detail="Busca semântica de catálogo indisponível neste ambiente.",
        ) from exc

    vec = VectorIndexAdapter(db_path)
    ranker = HybridRankingAdapter(repo)

    builder = CatalogBuilderService(source, repo, repo, normalizer)
    search = ProductSearchService(bm25, vec, ranker, repo)
    
    return builder, search, repo

# --- Endpoints ---

@router.get("/status")
async def get_catalog_status(deps=Depends(get_services)):
    _, _, repo = deps
    active_version = await repo.get_active_version()
    return {
        "active_version": active_version,
        "status": "ready" if active_version else "empty"
    }

@router.post("/rebuild")
async def rebuild_catalog(req: RebuildRequest, background_tasks: BackgroundTasks, deps=Depends(get_services)):
    builder, _, _ = deps
    
    # Executar em background pois pode levar 2 minutos
    background_tasks.add_task(builder.rebuild_catalog, req.description)
    
    return {"message": "Catalog rebuild started in background.", "description": req.description}

@router.post("/search")
async def search_catalog(req: SearchRequest, deps=Depends(get_services)):
    _, search_service, _ = deps
    
    results = await search_service.search_deep(req.query, top_k=req.limit)
    
    output = []
    for res in results:
        p = res.product
        output.append({
            "product_id": p.product_id,
            "name": p.name_canonical,
            "brand": p.brand,
            "category": p.category,
            "score": res.scores.final,
            "rationale": res.rationale
        })
        
    return {"query": req.query, "results": output}

@router.get("/versions")
async def list_versions(deps=Depends(get_services)):
    _, _, repo = deps
    versions = await repo.list_versions()
    return {"versions": versions, "count": len(versions)}
