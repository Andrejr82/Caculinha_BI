"""
BM25IndexAdapter — Adaptador de Busca Lexical (BM25)

Implementa indexação e busca textual utilizando a extensão Full-Text Search (FTS) do DuckDB.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import duckdb
from typing import List, Optional
import structlog
from pathlib import Path

from backend.domain.entities.retrieval import RetrievedItem
from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.ports.product_search_ports import IRetrievalIndexPort

logger = structlog.get_logger(__name__)

class BM25IndexAdapter(IRetrievalIndexPort):
    """
    Adaptador que utiliza DuckDB FTS para busca BM25.
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._initialize_fts()

    def _initialize_fts(self):
        """Garante que a extensão FTS está carregada."""
        with duckdb.connect(str(self.db_path)) as con:
            con.execute("INSTALL fts; LOAD fts;")

    async def build_index(self, products: List[ProductCanonical] = None, version: str = None) -> bool:
        """
        Cria o índice FTS para a tabela de produtos canônicos.
        """
        logger.info("building_bm25_index_defensive", version=version)
        
        try:
            with duckdb.connect(str(self.db_path)) as con:
                con.execute("INSTALL fts; LOAD fts;")
                
                # O DuckDB FTS pode falhar se houver metadados órfãos.
                # Tentamos dropar explicitamente antes de criar.
                try:
                    con.execute("CALL drop_fts_index('products_canonical')")
                except:
                    pass
                
                # Criar novo índice usando PRAGMA (mais direto em algumas versões)
                # target_table, id_column, *search_columns
                con.execute(f"""
                    CALL create_fts_index(
                        'products_canonical', 
                        'product_id', 
                        'name_canonical', 'brand', 'category', 'searchable_text',
                        overwrite=1,
                        stemmer='portuguese'
                    )
                """)
                
            logger.info("bm25_index_built_successfully")
            return True
        except Exception as e:
            logger.error("bm25_index_build_failed", error=str(e))
            # Fallback: Se o erro for de catálogo, tentamos ignorar se a busca funcionar
            return False
        except Exception as e:
            logger.error("bm25_index_build_failed", error=str(e))
            return False

    async def search(self, query: str, version: str, top_k: int = 100) -> List[RetrievedItem]:
        """
        Realiza a busca BM25 filtrando pela versão ativa do catálogo.
        """
        if not query:
            return []
            
        logger.info("bm25_search_started", query=query, version=version)
        
        # Limpar query (o FTS do DuckDB é sensível a caracteres especiais)
        clean_query = query.replace("'", " ").replace("-", " ")
        
        sql = f"""
            SELECT 
                product_id, 
                score as fts_score
            FROM (
                SELECT *, fts_main_products_canonical.match_bm25(
                    product_id, 
                    '{clean_query}'
                ) AS score
                FROM products_canonical
                WHERE catalog_version = '{version}'
            ) sq
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT {top_k}
        """
        
        try:
            with duckdb.connect(str(self.db_path)) as con:
                con.execute("LOAD fts;")
                df = con.execute(sql).df()
                
                results = []
                for _, row in df.iterrows():
                    results.append(RetrievedItem(
                        product_id=int(row['product_id']),
                        score=float(row['fts_score']),
                        source='bm25'
                    ))
                
                logger.info("bm25_search_completed", results_count=len(results))
                return results
        except Exception as e:
            logger.error("bm25_search_failed", error=str(e))
            return []
