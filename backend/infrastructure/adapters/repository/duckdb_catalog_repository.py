"""
DuckDBCatalogRepository — Repositório de Catálogo via DuckDB

Implementa persistência versionada para produtos canônicos e sinônimos.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import duckdb
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import structlog
from pathlib import Path

from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.entities.synonym import CanonicalTerm
from backend.domain.ports.product_catalog_ports import IProductCatalogRepository, ISynonymRepository, ICatalogVersionPort

logger = structlog.get_logger(__name__)

class DuckDBCatalogRepository(IProductCatalogRepository, ISynonymRepository, ICatalogVersionPort):
    """
    Implementação DuckDB para o catálogo semântico.
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._ensure_tables()

    def _ensure_tables(self):
        """Cria as tabelas necessárias se não existirem."""
        with duckdb.connect(str(self.db_path)) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS catalog_versions (
                    version_id TEXT PRIMARY KEY,
                    description TEXT,
                    created_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS products_canonical (
                    product_id BIGINT,
                    name_raw TEXT,
                    name_canonical TEXT,
                    brand TEXT,
                    dept TEXT,
                    category TEXT,
                    subcategory TEXT,
                    attributes_json TEXT,
                    status TEXT,
                    updated_at TIMESTAMP,
                    searchable_text TEXT,
                    catalog_version TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_prod_version ON products_canonical(catalog_version);
                
                CREATE TABLE IF NOT EXISTS synonyms (
                    term TEXT PRIMARY KEY,
                    synonyms TEXT -- JSON list
                );
            """)

    async def save_products(self, products: List[ProductCanonical], version: str) -> bool:
        """Salva produtos em lote (obsoleto/lento para 1M+)."""
        data = [p.to_dict() for p in products]
        df = pd.DataFrame(data)
        return await self.save_products_df(df, version)

    async def save_products_df(self, df: "pd.DataFrame", version: str) -> bool:
        """
        Salva um DataFrame de produtos diretamente.
        Ultra-rápido via DuckDB integration.
        """
        if df.empty:
            return True
            
        logger.info("saving_dataframe_to_duckdb", rows=len(df), version=version)
        
        # Garantir colunas necessárias e serialização
        # (Presumimos que o chamador já preparou o DF para performance)
        
        try:
            with duckdb.connect(str(self.db_path)) as con:
                con.execute("INSERT INTO products_canonical SELECT * FROM df")
            return True
        except Exception as e:
            logger.error("duckdb_df_save_failed", error=str(e))
            return False

    async def get_product(self, product_id: int, version: str) -> Optional[ProductCanonical]:
        with duckdb.connect(str(self.db_path)) as con:
            res = con.execute("""
                SELECT * FROM products_canonical 
                WHERE product_id = ? AND catalog_version = ?
            """, [product_id, version]).df()
            
            if res.empty:
                return None
            
            data = res.iloc[0].to_dict()
            data['attributes_json'] = json.loads(data['attributes_json'])
            return ProductCanonical.from_dict(data)

    async def list_products(self, version: str, limit: int = 100, offset: int = 0) -> List[ProductCanonical]:
        with duckdb.connect(str(self.db_path)) as con:
            df = con.execute("""
                SELECT * FROM products_canonical 
                WHERE catalog_version = ?
                LIMIT ? OFFSET ?
            """, [version, limit, offset]).df()
            
            products = []
            for _, row in df.iterrows():
                data = row.to_dict()
                data['attributes_json'] = json.loads(data['attributes_json'])
                products.append(ProductCanonical.from_dict(data))
            return products

    # Implementation of ICatalogVersionPort
    async def create_version(self, description: str) -> str:
        from uuid import uuid4
        v_id = f"cat-{uuid4().hex[:8]}"
        created_at = datetime.utcnow()
        
        with duckdb.connect(str(self.db_path)) as con:
            con.execute("""
                INSERT INTO catalog_versions (version_id, description, created_at)
                VALUES (?, ?, ?)
            """, [v_id, description, created_at])
            
        return v_id

    async def activate_version(self, version: str) -> bool:
        with duckdb.connect(str(self.db_path)) as con:
            con.execute("UPDATE catalog_versions SET is_active = FALSE")
            con.execute("UPDATE catalog_versions SET is_active = TRUE WHERE version_id = ?", [version])
        return True

    async def get_active_version(self) -> Optional[str]:
        with duckdb.connect(str(self.db_path)) as con:
            res = con.execute("SELECT version_id FROM catalog_versions WHERE is_active = TRUE").fetchone()
            return res[0] if res else None

    async def rollback_to_previous(self) -> Optional[str]:
        with duckdb.connect(str(self.db_path)) as con:
            versions = con.execute("SELECT version_id FROM catalog_versions ORDER BY created_at DESC LIMIT 2").fetchall()
            if len(versions) < 2:
                return None
            prev_version = versions[1][0]
            await self.activate_version(prev_version)
            return prev_version

    # Implementation of ISynonymRepository
    async def save_synonyms(self, synonyms: List[CanonicalTerm]) -> bool:
        with duckdb.connect(str(self.db_path)) as con:
            for s in synonyms:
                con.execute("""
                    INSERT OR REPLACE INTO synonyms (term, synonyms)
                    VALUES (?, ?)
                """, [s.term, json.dumps(s.synonyms)])
        return True

    async def get_synonyms_for_term(self, term: str) -> List[str]:
        with duckdb.connect(str(self.db_path)) as con:
            res = con.execute("SELECT synonyms FROM synonyms WHERE term = ?", [term]).fetchone()
            return json.loads(res[0]) if res else []
