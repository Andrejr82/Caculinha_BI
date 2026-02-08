"""
ProductSearchService — Serviço de Busca de Produtos

Orquestra BM25, Vetores e Ranking Híbrido para prover resultados de alta 
qualidade ao Agente de IA.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import structlog
from typing import List, Dict, Any, Optional
from backend.domain.entities.retrieval import RankedProduct
from backend.domain.ports.product_search_ports import (
    IRetrievalIndexPort, 
    IRankingFusionPort
)
from backend.domain.ports.product_catalog_ports import IProductCatalogRepository

logger = structlog.get_logger(__name__)

class ProductSearchService:
    """
    Serviço de aplicação que coordena a busca profunda no catálogo.
    """
    
    def __init__(
        self,
        bm25_adapter: IRetrievalIndexPort,
        vector_adapter: IRetrievalIndexPort,
        ranker: IRankingFusionPort,
        repository: IProductCatalogRepository
    ):
        self.bm25_adapter = bm25_adapter
        self.vector_adapter = vector_adapter
        self.ranker = ranker
        self.repository = repository

    async def search_deep(self, query: str, top_k: int = 10, weights: Optional[Dict[str, float]] = None) -> List[RankedProduct]:
        """
        Realiza a busca híbrida completa.
        """
        import time
        start_time = time.perf_counter()
        logger.info("deep_search_started", query=query)
        
        # 1. Obter versão ativa
        active_version = await self.repository.get_active_version()
        if not active_version:
            logger.error("deep_search_failed_no_active_version")
            return []
            
        # 2. Executar buscas em paralelo (Retrieval)
        import asyncio
        p_start = time.perf_counter()
        bm25_task = self.bm25_adapter.search(query, active_version, top_k=50)
        vector_task = self.vector_adapter.search(query, active_version, top_k=50)
        
        bm25_res, vector_res = await asyncio.gather(bm25_task, vector_task)
        p_end = time.perf_counter()
        
        # 3. Fusão e Ranking
        f_start = time.perf_counter()
        ranked_products = await self.ranker.fuse_and_rank(
            bm25_results=bm25_res,
            vector_results=vector_res,
            query=query,
            weights=weights
        )
        f_end = time.perf_counter()
        
        total_time = time.perf_counter() - start_time
        logger.info(
            "deep_search_completed", 
            total_duration_ms=total_time*1000,
            retrieval_duration_ms=(p_end-p_start)*1000,
            fusion_duration_ms=(f_end-f_start)*1000,
            results_count=len(ranked_products)
        )
        
        return ranked_products[:top_k]
