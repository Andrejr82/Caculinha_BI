"""
HybridRankingAdapter — Adaptador de Fusão de Ranking

Implementa a combinação de resultados BM25 e Vetoriais utilizando 
Reciprocal Rank Fusion (RRF) e Boosts de Regras de Negócio.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import structlog
from typing import List, Dict, Any, Optional
from backend.domain.entities.retrieval import RetrievedItem, RankingScores, RankedProduct
from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.ports.product_search_ports import IRankingFusionPort
from backend.domain.ports.product_catalog_ports import IProductCatalogRepository

logger = structlog.get_logger(__name__)

class HybridRankingAdapter(IRankingFusionPort):
    """
    Realiza a fusão de resultados de diferentes motores de busca.
    """
    
    def __init__(self, catalog_repo: IProductCatalogRepository):
        self.catalog_repo = catalog_repo

    async def fuse_and_rank(
        self, 
        bm25_results: List[RetrievedItem], 
        vector_results: List[RetrievedItem],
        query: str,
        weights: Optional[Dict[str, float]] = None
    ) -> List[RankedProduct]:
        """
        Combina os rankings usando weighted score e RRF.
        Fórmula: ScoreFinal = w_bm25 * norm(bm25) + w_vec * norm(vector)
        """
        logger.info("hybrid_fusion_started", query=query, bm25_count=len(bm25_results), vector_count=len(vector_results))
        
        if not weights:
            weights = {"bm25": 0.6, "vector": 0.4}
            
        # 1. Mapear scores por Product ID
        combined: Dict[int, RankingScores] = {}
        
        # Normalização simples (Min-Max ou Rank-based)
        # Usaremos Rank-based RRF simplificado para robustez
        def apply_rrf(results: List[RetrievedItem], weight: float, source: str):
            for rank, item in enumerate(results):
                p_id = item.product_id
                if p_id not in combined:
                    combined[p_id] = RankingScores()
                
                # RRF Score: weight * (1 / (rank + 60))
                # Aqui usaremos o score bruto normalizado se disponível
                rrf_val = weight * (1.0 / (rank + 60))
                
                if source == 'bm25':
                    combined[p_id].bm25 = item.score
                    combined[p_id].final += rrf_val
                else:
                    combined[p_id].vector = item.score
                    combined[p_id].final += rrf_val

        apply_rrf(bm25_results, weights['bm25'], 'bm25')
        apply_rrf(vector_results, weights['vector'], 'vector')
        
        # 2. Ordenar por score final
        sorted_ids = sorted(combined.items(), key=lambda x: x[1].final, reverse=True)
        
        # 3. Encarregar detalhes do catálogo (Top N)
        # Limitamos a busca de detalhes para performance
        target_version = "cat-fda943ce"  # Idealmente passado no contexto, usaremos mock por agora
        # TODO: Resolver versão dinâmica no Orchestrator
        
        ranked_products = []
        for p_id, scores in sorted_ids[:50]:
            # Nota: O repositório precisa da versão. Buscaremos a ativa.
            version = await self.catalog_repo.get_active_version()
            product = await self.catalog_repo.get_product(p_id, version)
            
            if product:
                # 4. Aplicar Boosts de Regra de Negócio
                # Boost por marca se query contiver marca
                if product.brand and product.brand.lower() in query.lower():
                    scores.rules += 0.2
                    scores.final += 0.05  # Slight boost to final score
                
                ranked_products.append(RankedProduct(
                    product=product,
                    scores=scores,
                    rationale=f"Fusion Match (BM25: {scores.bm25:.2f}, Vector: {scores.vector:.2f})"
                ))
        
        logger.info("hybrid_fusion_completed", final_count=len(ranked_products))
        return ranked_products
