"""
Ferramenta de Busca no Catálogo Canônico

Permite ao Agente realizar buscas semânticas e lexicais profundas no 
catálogo de 1.1M+ produtos.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import List, Dict, Any, Optional
import structlog
from backend.application.services.product_search_service import ProductSearchService

logger = structlog.get_logger(__name__)

def create_catalog_search_tool(search_service: ProductSearchService):
    """
    Factory para criar a ferramenta de busca no catálogo.
    """
    
    async def pesquisar_produto_catalogo_profundo(
        query: str, 
        limite: int = 5
    ) -> str:
        """
        Realiza uma busca profunda no catálogo utilizando ranking híbrido.
        Use esta ferramenta quando precisar encontrar IDs de produtos ou validar
        se um produto existe no mix da empresa.
        
        Args:
            query: Texto da busca (ex: "bola de futebol", "caneta bic azul")
            limite: Quantidade de resultados (default 5)
            
        Returns:
            Uma string formatada com os produtos encontrados e seus IDs.
        """
        logger.info("tool_catalog_search_called", query=query, limit=limite)
        
        try:
            results = await search_service.search_deep(query, top_k=limite)
            
            if not results:
                return f"Nenhum produto encontrado para: '{query}'"
                
            output = [f"Resultados encontrados para '{query}':"]
            for i, res in enumerate(results):
                p = res.product
                output.append(
                    f"{i+1}. [ID: {p.product_id}] {p.name_canonical} | "
                    f"Marca: {p.brand} | Cat: {p.category} "
                    f"(Score: {res.scores.final:.2f})"
                )
                
            return "\n".join(output)
            
        except Exception as e:
            logger.error("tool_catalog_search_failed", error=str(e))
            return f"Erro ao pesquisar no catálogo: {str(e)}"

    return pesquisar_produto_catalogo_profundo
