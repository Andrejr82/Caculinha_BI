"""
ProductSourceParquetAdapter — Adaptador de Extração Parquet

Implementa a extração de dados brutos de produtos a partir do arquivo admmat.parquet 
utilizando DuckDB para máxima performance.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import duckdb
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from pathlib import Path

from backend.domain.ports.product_catalog_ports import IProductSourcePort

logger = structlog.get_logger(__name__)

class ProductSourceParquetAdapter(IProductSourcePort):
    """
    Adaptador que lê dados de produtos do arquivo Parquet.
    
    Regras:
    - Somente leitura do arquivo admmat.parquet.
    - Utiliza DuckDB para extração eficiente.
    """
    
    def __init__(self, parquet_path: str):
        self.parquet_path = Path(parquet_path)
        if not self.parquet_path.exists():
            logger.error("parquet_file_not_found", path=str(self.parquet_path))
            raise FileNotFoundError(f"Arquivo Parquet não encontrado: {self.parquet_path}")

    async def load_full_catalog(self) -> List[Dict[str, Any]]:
        """
        Carrega todos os produtos disponíveis na base.
        Detecta colunas disponíveis para evitar erros de schema.
        """
        logger.info("loading_full_parquet_catalog", path=str(self.parquet_path))
        
        info = self.get_schema_info()
        available_cols = info.get("columns", [])
        
        # Mapeamento de colunas desejadas vs reais
        mapping = {
            "PRODUTO": "product_id",
            "NOME": "name_raw",
            "MARCA": "brand",
            "NOMESEGMENTO": "dept",
            "NOMEGRUPOMAT": "category",
            "NOMESUBGRUPOMAT": "subcategory",
            "NOMEFAMILIAMAT": "family",
            "updated_at": "updated_at"
        }
        
        select_parts = []
        for col, alias in mapping.items():
            if col in available_cols:
                select_parts.append(f"{col} as {alias}")
            else:
                logger.warning("column_missing_in_parquet", column=col)
                # Fallback para string vazia ou default
                select_parts.append(f"'' as {alias}")
        
        query = f"SELECT {', '.join(select_parts)} FROM read_parquet('{self.parquet_path}')"
        
        try:
            items = duckdb.query(query).to_df().to_dict('records')
            logger.info("parquet_catalog_loaded", count=len(items))
            return items
        except Exception as e:
            logger.error("parquet_load_failed", error=str(e), query=query)
            return []

    async def load_incremental_catalog(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Carrega apenas registros alterados desde 'since'.
        """
        logger.info("loading_incremental_parquet_catalog", since=since.isoformat())
        
        info = self.get_schema_info()
        available_cols = info.get("columns", [])
        
        mapping = {
            "PRODUTO": "product_id",
            "NOME": "name_raw",
            "MARCA": "brand",
            "NOMESEGMENTO": "dept",
            "NOMEGRUPOMAT": "category",
            "NOMESUBGRUPOMAT": "subcategory",
            "NOMEFAMILIAMAT": "family",
            "updated_at": "updated_at"
        }
        
        select_parts = []
        for col, alias in mapping.items():
            if col in available_cols:
                select_parts.append(f"{col} as {alias}")
            else:
                select_parts.append(f"'' as {alias}")

        if "updated_at" not in available_cols:
            logger.warning("incremental_load_impossible_missing_updated_at")
            return await self.load_full_catalog()

        query = f"""
            SELECT {', '.join(select_parts)} 
            FROM read_parquet('{self.parquet_path}')
            WHERE updated_at > '{since.isoformat()}'
        """
        
        try:
            items = duckdb.query(query).to_df().to_dict('records')
            logger.info("parquet_incremental_loaded", count=len(items))
            return items
        except Exception as e:
            logger.error("parquet_incremental_failed", error=str(e))
            return []

    def get_schema_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o esquema do arquivo."""
        try:
            schema = duckdb.query(f"DESCRIBE SELECT * FROM read_parquet('{self.parquet_path}')").to_df()
            total_rows = duckdb.query(f"SELECT COUNT(*) FROM read_parquet('{self.parquet_path}')").fetchone()[0]
            return {
                "columns": schema['column_name'].tolist(),
                "types": schema['column_type'].tolist(),
                "total_rows": total_rows
            }
        except Exception as e:
            logger.error("schema_inspection_failed", error=str(e))
            return {}
