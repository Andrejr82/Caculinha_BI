"""
WhooshBM25IndexAdapter — Adaptador de Busca Lexical (BM25) via Whoosh

Implementa indexação e busca textual utilizando a biblioteca Whoosh.
Ideal para ambientes onde extensões SQL nativas são instáveis.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import os
import structlog
from typing import List, Optional
from pathlib import Path
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer

from backend.domain.entities.retrieval import RetrievedItem
from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.ports.product_search_ports import IRetrievalIndexPort

logger = structlog.get_logger(__name__)

class WhooshBM25IndexAdapter(IRetrievalIndexPort):
    """
    Adaptador de busca lexical utilizando Whoosh.
    """
    
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        if not self.index_dir.exists():
            self.index_dir.mkdir(parents=True)
            
        # Schema: product_id (ID), content (TEXT com radicalizador PT-BR)
        self.analyzer = StemmingAnalyzer() # Usaremos o analyzer padrão (pode ser tunado para PT)
        self.schema = Schema(
            product_id=ID(stored=True, unique=True),
            catalog_version=ID(stored=True),
            content=TEXT(analyzer=self.analyzer, stored=False)
        )

    async def build_index(self, products: List[ProductCanonical], version: str) -> bool:
        """
        Cria ou atualiza o índice Whoosh.
        """
        logger.info("building_whoosh_index", count=len(products), version=version)
        
        try:
            if not exists_in(str(self.index_dir)):
                ix = create_in(str(self.index_dir), self.schema)
            else:
                ix = open_dir(str(self.index_dir))
                
            writer = ix.writer()
            
            for p in products:
                # Combinar campos para indexação textual
                content = f"{p.name_canonical} {p.brand} {p.category} {p.subcategory}"
                writer.update_document(
                    product_id=str(p.product_id),
                    catalog_version=version,
                    content=content
                )
                
            writer.commit()
            logger.info("whoosh_index_built_successfully")
            return True
        except Exception as e:
            logger.error("whoosh_index_build_failed", error=str(e))
            return False

    async def search(self, query: str, version: str, top_k: int = 100) -> List[RetrievedItem]:
        """
        Realiza a busca lexical.
        """
        if not query or not exists_in(str(self.index_dir)):
            return []
            
        logger.info("whoosh_search_started", query=query, version=version)
        
        try:
            ix = open_dir(str(self.index_dir))
            with ix.searcher() as searcher:
                # Parser para buscar no campo content
                parser = MultifieldParser(["content"], ix.schema)
                q = parser.parse(query)
                
                # Filtro por versão
                from whoosh.query import Term
                version_filter = Term("catalog_version", version)
                
                results = searcher.search(q, limit=top_k, filter=version_filter)
                
                retrieved = []
                for hit in results:
                    retrieved.append(RetrievedItem(
                        product_id=int(hit['product_id']),
                        score=float(hit.score),
                        source='bm25'
                    ))
                    
                logger.info("whoosh_search_completed", results_count=len(retrieved))
                return retrieved
        except Exception as e:
            logger.error("whoosh_search_failed", error=str(e))
            return []
