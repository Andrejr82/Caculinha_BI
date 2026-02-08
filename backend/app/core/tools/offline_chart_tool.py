import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

# Get singleton adapter instance
duckdb_adapter = get_duckdb_adapter()
from backend.app.core.utils.field_mapper import FieldMapper

logger = logging.getLogger(__name__)
field_mapper = FieldMapper()

@tool
def gerar_grafico_offline(
    tipo_grafico: str,
    metrica: str,
    dimensao: str,
    filtros: Optional[Dict[str, Any]] = None,
    limite: int = 100  # FIX 2026-01-27: Aumentado de 10 para 100 (consistência)
) -> str:
    """
    Gera um gráfico simples para o modo offline.
    
    USE QUANDO: A geração padrão de gráficos (online) falhar ou quando estiver sem conexão com LLM externo.
    Não use como primeira opção.

    Args:
        tipo_grafico: "bar" ou "line".
        metrica: Coluna de valor (ex: "venda", "estoque").
        dimensao: Coluna de categoria/tempo (ex: "grupo", "mes").
        filtros: Dicionário de filtros (ex: {"PRODUTO": 123}).
        limite: Top N resultados.
        
    Returns:
        String contendo o JSON do gráfico no formato Markdown (```json ... ```).
    """
    try:
        # 1. Mapear Termos
        real_metric = field_mapper.map_term(metrica) or "VENDA_30DD"
        real_dim = field_mapper.map_term(dimensao) or "PRODUTO"
        
        # Ajustes de Dimensão "Lojas" -> "UNE"
        if "loja" in dimensao.lower() or "filial" in dimensao.lower():
            real_dim = "UNE"

        # Ajustes de Agregação
        agg_func = "sum"
        if "estoque" in metrica.lower():
            agg_func = "sum"
            if not real_metric: real_metric = "ESTOQUE_UNE"
        elif "preço" in metrica.lower():
            agg_func = "avg"
            if not real_metric: real_metric = "LIQUIDO_38"
        
        # 2. Consultar Dados
        # Garantir que filtros não seja None para a query
        safe_filters = filtros if filtros else {}
        
        df = adapter.execute_aggregation(
            agg_col=real_metric,
            agg_func=agg_func,
            group_by=[real_dim],
            filters=safe_filters,
            limit=limite
        )
        
        if df.empty:
            return "Não foi possível gerar o gráfico: nenhum dado encontrado."
            
        # 3. Construir ECharts Option (Simplificado)
        # Formato esperado pelo ChatServiceV3 / Chat.tsx
        
        categorias = df[real_dim].astype(str).tolist()
        valores = df['valor'].tolist() if 'valor' in df.columns else df.iloc[:, 1].tolist()
        
        chart_spec = {
            "chart_type": tipo_grafico,
            "title": f"{metrica.title()} por {dimensao.title()}",
            "xAxis": {"type": "category", "data": categorias},
            "yAxis": {"type": "value"},
            "series": [{
                "data": valores,
                "type": "bar" if tipo_grafico == "bar" else "line",
                "name": metrica.title()
            }],
            "summary": {
                "mensagem": f"Aqui está o gráfico de {metrica} por {dimensao} (Top {limite}).",
                "total": sum(valores) if valores else 0
            }
        }
        
        # 4. Retornar JSON formatado em Markdown para o ChatServiceV3 detectar
        return f"```json\n{json.dumps({'chart_spec': chart_spec}, indent=2)}\n```"

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico offline: {e}", exc_info=True)
        return f"Erro ao gerar gráfico: {str(e)}"
