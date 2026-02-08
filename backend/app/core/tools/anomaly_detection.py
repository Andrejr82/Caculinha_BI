"""
Ferramenta de Detecção de Anomalias Estatísticas - Context7 2026
Usa DuckDB para cálculos de Z-Score e identificação de outliers.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def analisar_anomalias(
    metrica: str,
    dimensao: str,
    limite: int = 5,
    threshold: float = 2.0
) -> Dict[str, Any]:
    """
    Analisa anomalias estatísticas (outliers) em uma métrica agrupada por dimensão.
    Usa Z-Score para identificar desvios significativos da média.

    USE QUANDO: O usuário perguntar "anomalias em vendas", "vendas fora do normal",
    "comportamento atípico", "outliers de estoque", "lojas com performance estranha".
    Args:
        metrica: Coluna numérica a ser analisada (ex: "VENDA_30DD", "ESTOQUE_UNE")
        dimensao: Coluna de agrupamento (ex: "UNE", "NOMESEGMENTO")
        limite: Número máximo de anomalias a retornar
        threshold: Limite de desvios padrão (Z-Score) para considerar anomalia (default: 2.0)

    Returns:
        Lista de anomalias detectadas com Z-Score e explicação.
    """
    try:
        from backend.app.core.parquet_cache import cache
        from backend.app.core.utils.field_mapper import FieldMapper
        field_mapper = FieldMapper()

        # 1. Mapear colunas
        real_metrica = field_mapper.map_term(metrica) or metrica
        real_dimensao = field_mapper.map_term(dimensao) or dimensao
        
        table_name = cache._adapter.get_memory_table("admmat.parquet")
        
        logger.info(f"[ANOMALY] Analisando {real_metrica} por {real_dimensao} (Z > {threshold})")

        # 2. Query Estatística Avançada (DuckDB)
        # Calcula média e desvio padrão da população inteira
        stats_query = f"""
            WITH stats AS (
                SELECT 
                    AVG({real_metrica}) as media,
                    STDDEV({real_metrica}) as desvio
                FROM (
                    SELECT {real_dimensao}, SUM({real_metrica}) as {real_metrica}
                    FROM {table_name}
                    GROUP BY {real_dimensao}
                )
            ),
            grouped AS (
                SELECT {real_dimensao}, SUM({real_metrica}) as valor
                FROM {table_name}
                GROUP BY {real_dimensao}
            )
            SELECT 
                g.{real_dimensao},
                g.valor,
                s.media,
                s.desvio,
                (g.valor - s.media) / NULLIF(s.desvio, 0) as z_score
            FROM grouped g, stats s
            WHERE ABS((g.valor - s.media) / NULLIF(s.desvio, 0)) >= {threshold}
            ORDER BY ABS(z_score) DESC
            LIMIT {limite}
        """
        
        result = cache._adapter.query(stats_query)
        
        if hasattr(result, 'to_dict'):
            anomalias = result.to_dict(orient='records')
        elif hasattr(result, 'df'):
            anomalias = result.df().to_dict(orient='records')
        else:
            anomalias = [] # Fallback

        # 3. Formatar Resposta Narrativa
        if not anomalias:
            return {
                "anomalias": [],
                "mensagem": f"Nenhuma anomalia estatística encontrada para {metrica} (Z-Score < {threshold}). Os dados estão dentro do padrão normal."
            }

        mensagem = f"Detectei {len(anomalias)} anomalias significativas em {dimensao}:\n\n"
        for a in anomalias:
            desvio_pct = ((a['valor'] - a['media']) / a['media']) * 100
            direcao = "acima" if a['z_score'] > 0 else "abaixo"
            # Formatar para o usuário
            val_format = f"{a['valor']:,.0f}"
            mensagem += f"- **{a[real_dimensao]}**: {val_format} ({desvio_pct:+.1f}% da média). Z-Score: {a['z_score']:.1f} (Anomalia {direcao}).\n"

        return {
            "anomalias": anomalias,
            "mensagem": mensagem,
            "estatisticas": {
                "metrica": metrica,
                "dimensao": dimensao,
                "threshold_z": threshold
            }
        }

    except Exception as e:
        logger.error(f"[ANOMALY] Erro: {e}")
        return {"error": str(e)}
