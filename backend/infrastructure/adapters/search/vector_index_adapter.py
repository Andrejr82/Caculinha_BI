"""
VectorIndexAdapter — Adaptador de Busca Vetorial (Semântica)

Implementa indexação e busca por similaridade semântica utilizando 
sentence-transformers e DuckDB.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import duckdb
import numpy as np
from typing import List, Optional, Dict, Any
import structlog
from pathlib import Path

from backend.domain.entities.retrieval import RetrievedItem
from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.ports.product_search_ports import IRetrievalIndexPort

logger = structlog.get_logger(__name__)
class VectorIndexAdapter(IRetrievalIndexPort):
    """
    Adaptador para busca semântica.
    Utiliza embeddings vetoriais persistidos no DuckDB.
    """
    
    def __init__(self, db_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = Path(db_path)
        self.model_name = model_name
        self._model = None # Lazy loading
        self._ensure_tables()

    @property
    def model(self):
        """Lazy loader para o modelo transformer."""
        if self._model is None:
            logger.info("loading_sentence_transformer_model", model=self.model_name)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _ensure_tables(self):
        """Cria tabela de embeddings se não existir."""
        with duckdb.connect(str(self.db_path)) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS products_embeddings (
                    product_id BIGINT,
                    embedding FLOAT[],
                    catalog_version TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_vec_version ON products_embeddings(catalog_version);
            """)

    async def build_index(self, products: List[ProductCanonical], version: str) -> bool:
        """
        Gera embeddings para os produtos e os salva no DuckDB.
        """
        if not products:
            return True
            
        logger.info("building_vector_index", count=len(products), version=version)
        
        try:
            # 1. Preparar textos para embedding
            texts = [p.searchable_text for p in products]
            ids = [p.product_id for p in products]
            
            # 2. Gerar embeddings (CPU por padrão)
            logger.info("generating_embeddings", model=self.model_name)
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # 3. Salvar no DuckDB
            data = []
            for i, product_id in enumerate(ids):
                data.append((product_id, embeddings[i].tolist(), version))
            
            import pandas as pd
            df = pd.DataFrame(data, columns=['product_id', 'embedding', 'catalog_version'])
            
            with duckdb.connect(str(self.db_path)) as con:
                # Limpar embeddings antigos da mesma versão se existirem
                con.execute("DELETE FROM products_embeddings WHERE catalog_version = ?", [version])
                con.execute("INSERT INTO products_embeddings SELECT * FROM df")
                
            logger.info("vector_index_built_successfully", rows=len(df))
            return True
        except Exception as e:
            logger.error("vector_index_build_failed", error=str(e))
            return False

    async def search(self, query: str, version: str, top_k: int = 100) -> List[RetrievedItem]:
        """
        Busca por similaridade de cosseno via SQL no DuckDB.
        """
        if not query:
            return []
            
        logger.info("vector_search_started", query=query, version=version)
        
        try:
            # 1. Gerar embedding da query
            query_embedding = self.model.encode(query).tolist()
            
            # 2. Busca via similaridade de cosseno (DuckDB suporta list_cosine_similarity)
            # Nota: O DuckDB precisa do array de floats como literal ou parâmetro.
            
            sql = f"""
                SELECT 
                    product_id, 
                    list_cosine_similarity(embedding, ?::FLOAT[]) as similarity
                FROM products_embeddings
                WHERE catalog_version = ?
                ORDER BY similarity DESC
                LIMIT ?
            """
            
            with duckdb.connect(str(self.db_path)) as con:
                df = con.execute(sql, [query_embedding, version, top_k]).df()
                
                results = []
                for _, row in df.iterrows():
                    results.append(RetrievedItem(
                        product_id=int(row['product_id']),
                        score=float(row['similarity']),
                        source='vector'
                    ))
                
                logger.info("vector_search_completed", results_count=len(results))
                return results
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []
