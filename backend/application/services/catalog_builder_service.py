"""
CatalogBuilderService — Serviço de Construção do Catálogo

Orquestra o pipeline: Source -> Extraction -> Normalization -> Persistence.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.ports.product_catalog_ports import (
    IProductSourcePort, 
    IProductCatalogRepository, 
    ICatalogVersionPort,
    INormalizationPort
)

logger = structlog.get_logger(__name__)

class CatalogBuilderService:
    """
    Serviço que reconstrói o catálogo canônico a partir da fonte bruta.
    """
    
    def __init__(
        self,
        source: IProductSourcePort,
        repository: IProductCatalogRepository,
        version_manager: ICatalogVersionPort,
        normalizer: INormalizationPort
    ):
        self.source = source
        self.repository = repository
        self.version_manager = version_manager
        self.normalizer = normalizer

    async def rebuild_catalog(self, description: str = "Full Catalog Rebuild") -> str:
        """
        Executa o pipeline completo de reconstrução (Vetorizado).
        """
        import pandas as pd
        import json
        logger.info("rebuild_catalog_started_vectorized", description=description)
        
        # 1. Criar nova versão
        catalog_version = await self.version_manager.create_version(description)
        
        # 2. Carregar dados brutos
        raw_items = await self.source.load_full_catalog()
        if not raw_items:
            return ""

        # Converter para DataFrame
        df = pd.DataFrame(raw_items)
        del raw_items
        
        # 3. Transformação Vetorizada
        logger.info("transforming_data_vectorized", rows=len(df))
        
        # Normalizar colunas principais
        df['name_canonical'] = self.normalizer.normalize_series(df['name_raw'])
        df['brand_norm'] = self.normalizer.normalize_series(df['brand'])
        df['cat_norm'] = self.normalizer.normalize_series(df['category'])
        
        # Texto de busca (concatenação vetorizada)
        df['searchable_text'] = (
            df['name_canonical'] + " " + 
            df['brand_norm'] + " " + 
            df['cat_norm']
        ).str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # Status e Versão
        df['status'] = 'active'
        df['catalog_version'] = catalog_version
        
        # Serializar atributos JSON (operação ligeiramente lenta, mas ok no contexto)
        df['attributes_json'] = "{}" 
        
        # Ajustar colunas para o esquema do Repo (DuckDB)
        # Ordem: product_id, name_raw, name_canonical, brand, dept, category, subcategory, attributes_json, status, updated_at, searchable_text, catalog_version
        output_df = df[[
            'product_id', 'name_raw', 'name_canonical', 'brand', 'dept', 
            'category', 'subcategory', 'attributes_json', 'status', 
            'updated_at', 'searchable_text', 'catalog_version'
        ]].copy()
        
        # 4. Salvar
        success = await self.repository.save_products_df(output_df, catalog_version)
        
        if success:
            await self.version_manager.activate_version(catalog_version)
            logger.info("rebuild_catalog_completed", version_id=catalog_version)
            return catalog_version
        else:
            logger.error("rebuild_failed_during_save")
            return ""
