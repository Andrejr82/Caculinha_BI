
import logging
import pandas as pd
from typing import Dict, Any, List
from backend.app.core.data_source_manager import get_data_manager

logger = logging.getLogger(__name__)

class DataAggregationService:
    """
    Serviço responsável por agregar e resumir dados do parquet
    para consumo eficiente por LLMs, evitando envio de grandes volumes de dados.
    """

    @staticmethod
    def get_retail_summary(limit_items: int = 15, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gera um resumo estatístico dos dados de varejo.
        
        Args:
            limit_items: Número de itens para listas de 'top' (vendas, estoque, etc).
            filters: Dicionário opcional com filtros (ex: {'segments': ['Papelaria']})
            
        Returns:
            Dict com totais, top vendas, rupturas e alertas.
        """
        from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
        from backend.app.config.settings import settings
        
        try:
            adapter = get_duckdb_adapter()
            
            # Resolver caminho do Parquet (usa configuração ou padrão)
            parquet_path = settings.PARQUET_FILE_PATH
            if not parquet_path or "parquet" not in str(parquet_path):
                parquet_path = "admmat.parquet"

            # Registrar view lazy para o arquivo
            table_name = adapter.scan_parquet(parquet_path)
            
            # Construir filtro de segmento
            segment_condition = "1=1"
            if filters and filters.get("segments"):
                segments = filters["segments"]
                if segments:
                    # Sanitização básica e normalização
                    safe_segments = []
                    for s in segments:
                        sanitized = str(s).replace("'", "''").strip()
                        safe_segments.append(f"'{sanitized}'")
                    segments_in = ", ".join(safe_segments)
                    # Usa TRIM para evitar problemas com espaços no banco
                    segment_condition = f"TRIM(NOMESEGMENTO) IN ({segments_in})"
            
            # 1. Totais Gerais (Query Agregada Única)
            # COALESCE(SUM(...), 0) para evitar NULL
            sql_totals = f"""
                SELECT 
                    COALESCE(SUM(TRY_CAST(VENDA_30DD AS DOUBLE)), 0) as total_sales,
                    COALESCE(SUM(TRY_CAST(ESTOQUE_UNE AS DOUBLE)), 0) as total_stock,
                    COALESCE(SUM(TRY_CAST(ESTOQUE_UNE AS DOUBLE) * TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE)), 0) as stock_value
                FROM {table_name}
                WHERE {segment_condition}
            """
            totals = adapter.query_dict(sql_totals)[0]

            # 2. Top Vendas (Limitado a N registros)
            sql_top_sales = f"""
                SELECT PRODUTO, NOME, NOMESEGMENTO, VENDA_30DD, ESTOQUE_UNE, LIQUIDO_38
                FROM {table_name}
                WHERE TRY_CAST(VENDA_30DD AS DOUBLE) > 0
                  AND {segment_condition}
                ORDER BY TRY_CAST(VENDA_30DD AS DOUBLE) DESC
                LIMIT {limit_items}
            """
            top_sales = adapter.query_dict(sql_top_sales)

            # 3. Rupturas (%ABAST <= 50% - Guia UNE: ESTOQUE_UNE <= 50% LINHA_VERDE)
            sql_stockouts = f"""
                SELECT PRODUTO, NOME, NOMESEGMENTO, NOMEFABRICANTE, VENDA_30DD, ESTOQUE_UNE, ESTOQUE_LV,
                       ROUND(TRY_CAST(ESTOQUE_UNE AS DOUBLE) / NULLIF(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) * 100, 2) as PERC_ABAST
                FROM {table_name}
                WHERE TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0 
                  AND (TRY_CAST(ESTOQUE_UNE AS DOUBLE) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5
                  AND {segment_condition}
                ORDER BY TRY_CAST(VENDA_30DD AS DOUBLE) DESC
                LIMIT {limit_items}
            """
            stockouts = adapter.query_dict(sql_stockouts)

            # 4. Estoque Parado (Venda = 0 e Estoque > 100)
            sql_dead_stock = f"""
                SELECT PRODUTO, NOME, NOMESEGMENTO, VENDA_30DD, ESTOQUE_UNE, ULTIMA_ENTRADA_CUSTO_CD
                FROM {table_name}
                WHERE TRY_CAST(VENDA_30DD AS DOUBLE) = 0 AND TRY_CAST(ESTOQUE_UNE AS DOUBLE) > 100
                  AND {segment_condition}
                ORDER BY TRY_CAST(ESTOQUE_UNE AS DOUBLE) DESC
                LIMIT {limit_items}
            """
            dead_stock = adapter.query_dict(sql_dead_stock)

            return {
                "general_stats": {
                    "total_sales_30d": totals.get("total_sales", 0),
                    "total_stock_units": totals.get("total_stock", 0),
                    "stock_financial_value": totals.get("stock_value", 0)
                },
                "top_performing_products": top_sales,
                "critical_measurements": {
                    "stockouts": stockouts,
                    "dead_stock": dead_stock
                },
                "available_data_columns": ["PRODUTO", "NOME", "NOMESEGMENTO", "VENDA_30DD", "ESTOQUE_UNE", "LIQUIDO_38", "ULTIMA_ENTRADA_CUSTO_CD"]
            }

        except Exception as e:
            logger.error(f"Erro na agregação de dados (DuckDB): {e}")
            # Fallback seguro para não crashar a UI
            return {
                "general_stats": {"total_sales_30d": 0, "total_stock_units": 0, "stock_financial_value": 0},
                "top_performing_products": [],
                "critical_measurements": {"stockouts": [], "dead_stock": []},
                "error": str(e)
            }

