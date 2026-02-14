"""
Query Router - Sistema de Roteamento Inteligente de Queries para Ferramentas
Mapeia intenção + contexto → ferramenta específica + parâmetros extraídos.

Author: Backend Specialist Agent
Date: 2026-01-24
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from backend.app.core.utils.intent_classifier import IntentType

logger = logging.getLogger(__name__)


@dataclass
class ToolSelection:
    """Resultado do roteamento de query."""
    tool_name: str
    tool_params: Dict[str, Any]
    confidence: float  # 0.0 - 1.0
    fallback_tools: List[str]
    reasoning: str  # Explicação da decisão


# Mapeamento de Intent → Ferramenta Principal
INTENT_TO_TOOL_MAP = {
    IntentType.VISUALIZATION: "gerar_grafico_universal_v2",
    IntentType.FORECASTING: "prever_demanda_sazonal",
    IntentType.CALCULATION: "calcular_eoq",  # Default, será refinado
    IntentType.ANOMALY_DETECTION: "detectar_anomalias_vendas",
    IntentType.OPTIMIZATION: "alocar_estoque_lojas",  # Default, será refinado
    IntentType.ANALYSIS: "analisar_produto_todas_lojas",  # Default, será refinado
    IntentType.DATA_QUERY: "consultar_dados_flexivel",
    IntentType.METADATA: "consultar_dicionario_dados",
}


def extract_une_filter(query: str) -> Optional[str]:
    """Extrai código UNE da query."""
    # Padrões: "une 520", "loja 520", "na 520"
    patterns = [
        r"u+ne\s+(\d+)",  # tolera typo: uune, uuune...
        r"une\s+(\d+)",
        r"loja\s+(\d+)",
        r"na\s+(\d{3,4})",  # Assume UNE tem 3-4 dígitos
        r"da\s+(\d{3,4})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            une = match.group(1)
            logger.debug(f"[ROUTER] Extracted UNE: {une}")
            return une
    
    return None


def extract_product_code(query: str) -> Optional[int]:
    """Extrai código de produto da query."""
    # Padrões: "produto 25", "SKU 369947", "item 123"
    patterns = [
        r"produto\s+(\d+)",
        r"sku\s+(\d+)",
        r"item\s+(\d+)",
        r"c[oó]digo\s+(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            code = int(match.group(1))
            logger.debug(f"[ROUTER] Extracted product code: {code}")
            return code
    
    return None


def extract_segment_filter(query: str) -> Optional[str]:
    """Extrai nome de segmento da query."""
    # Padrão: "segmento X", "do segmento Y"
    patterns = [
        r"segmento\s+(\w+)",
        r"d[oa]\s+segmento\s+(\w+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            segment = match.group(1).upper()
            logger.debug(f"[ROUTER] Extracted segment: {segment}")
            return segment
    
    return None


def extract_top_limit(query: str) -> Optional[int]:
    """Extrai limite de top N da query."""
    # Padrões: "top 10", "5 maiores", "3 principais"
    patterns = [
        r"top\s+(\d+)",
        r"(\d+)\s+maiores",
        r"(\d+)\s+menores",
        r"(\d+)\s+principais",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            limit = int(match.group(1))
            logger.debug(f"[ROUTER] Extracted limit: {limit}")
            return limit
    
    # Default para rankings
    if "ranking" in query.lower():
        return 10
    
    return None


def extract_days_param(query: str) -> Optional[int]:
    """Extrai número de dias da query."""
    # Padrões: "30 dias", "próximos 60 dias", "últimos 90 dias"
    patterns = [
        r"(\d+)\s+dias",
        r"pr[oó]ximos?\s+(\d+)\s+dias",
        r"[uú]ltimos?\s+(\d+)\s+dias",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            days = int(match.group(1))
            logger.debug(f"[ROUTER] Extracted days: {days}")
            return days
    
    return None


def route_visualization(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para visualizações."""
    query_lower = query.lower()
    
    # Sub-classificação
    if "dashboard" in query_lower:
        return ToolSelection(
            tool_name="gerar_dashboard_executivo",
            tool_params={},
            confidence=confidence * 0.95,
            fallback_tools=["gerar_grafico_universal_v2"],
            reasoning="Dashboard executivo detectado"
        )
    
    # Default: gerar_grafico_universal_v2 (ferramenta universal)
    params = {
        "descricao": query,
        "tipo_grafico": "auto"
    }
    
    # Extrair filtros
    une = extract_une_filter(query)
    if une:
        params["filtro_une"] = une  # String (UNE codes are strings)
    
    segment = extract_segment_filter(query)
    if segment:
        params["filtro_segmento"] = segment  # String
    
    product = extract_product_code(query)
    if product:
        # String para maior compatibilidade com providers que validam schema estritamente.
        params["filtro_produto"] = str(product)
    
    limit = extract_top_limit(query)
    if limit:
        # Enviar como string reduz falhas de tool-call em providers estritos.
        params["limite"] = str(limit)
    
    # Detectar tipo de gráfico
    if "pizza" in query_lower or "pie" in query_lower:
        params["tipo_grafico"] = "pie"
    elif "linha" in query_lower or "line" in query_lower:
        params["tipo_grafico"] = "line"
    else:
        params["tipo_grafico"] = "bar"  # Default para rankings
    
    return ToolSelection(
        tool_name="gerar_grafico_universal_v2",
        tool_params=params,
        confidence=confidence,
        fallback_tools=["gerar_ranking_produtos_mais_vendidos", "gerar_visualizacao_customizada"],
        reasoning=f"Visualização com filtros: {list(params.keys())}"
    )


def route_forecasting(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para previsões."""
    query_lower = query.lower()
    
    product = extract_product_code(query)
    days = extract_days_param(query) or 30  # Default 30 dias
    
    # Detectar sazonalidade explícita
    seasonal_keywords = ["natal", "volta às aulas", "volta as aulas", "páscoa", "pascoa", "black friday"]
    has_seasonal = any(kw in query_lower for kw in seasonal_keywords)
    
    if has_seasonal or "sazonal" in query_lower:
        tool_name = "prever_demanda_sazonal"
        reasoning = "Previsão com sazonalidade detectada"
    elif "tendência" in query_lower or "regressão" in query_lower:
        tool_name = "analise_regressao_vendas"
        reasoning = "Análise de tendência via regressão"
    else:
        tool_name = "prever_demanda_sazonal"  # Default
        reasoning = "Previsão de demanda padrão"
    
    params = {}
    if product:
        params["produto_codigo"] = product
    if tool_name == "prever_demanda_sazonal":
        params["dias_previsao"] = days
    elif tool_name == "analise_regressao_vendas":
        params["dias_analise"] = days
        params["dias_forecast"] = 30
    
    return ToolSelection(
        tool_name=tool_name,
        tool_params=params,
        confidence=confidence,
        fallback_tools=["analisar_historico_vendas"],
        reasoning=reasoning
    )


def route_calculation(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para cálculos."""
    query_lower = query.lower()
    
    product = extract_product_code(query)
    une = extract_une_filter(query)
    
    # Sub-classificação de cálculo
    if "eoq" in query_lower or "lote econômico" in query_lower or "quanto comprar" in query_lower:
        tool_name = "calcular_eoq"
        params = {}
        if product:
            params["produto_codigo"] = product
        reasoning = "Cálculo de EOQ (lote econômico)"
        
    elif "margem" in query_lower or "mc" in query_lower:
        tool_name = "calcular_mc_produto"
        params = {}
        if product:
            params["produto_codigo"] = product
        if une:
            params["une"] = int(une)
        reasoning = "Cálculo de margem de contribuição"
        
    elif "preço final" in query_lower or "preco final" in query_lower:
        tool_name = "calcular_preco_final_une"
        params = {}
        if product:
            params["produto_codigo"] = product
        if une:
            params["une"] = int(une)
        reasoning = "Cálculo de preço final"
        
    else:
        # Fallback genérico
        tool_name = "calcular_eoq"
        params = {}
        if product:
            params["produto_codigo"] = product
        reasoning = "Cálculo genérico (fallback para EOQ)"
    
    return ToolSelection(
        tool_name=tool_name,
        tool_params=params,
        confidence=confidence * 0.9,  # Reduz confiança se foi fallback
        fallback_tools=["consultar_dados_flexivel"],
        reasoning=reasoning
    )


def route_anomaly_detection(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para detecção de anomalias."""
    product = extract_product_code(query)
    days = extract_days_param(query) or 90  # Default 90 dias para anomalias
    
    params = {
        "dias_analise": days,
        "sensibilidade": 2.5  # Default moderado
    }
    
    if product:
        params["produto_codigo"] = product
    
    # Detectar sensibilidade
    if "extremo" in query.lower() or "muito anormal" in query.lower():
        params["sensibilidade"] = 3.0
    elif "leve" in query.lower() or "pequeno" in query.lower():
        params["sensibilidade"] = 2.0
    
    return ToolSelection(
        tool_name="detectar_anomalias_vendas",
        tool_params=params,
        confidence=confidence,
        fallback_tools=["analisar_anomalias"],
        reasoning=f"Detecção de anomalias com sensibilidade {params['sensibilidade']}"
    )


def route_optimization(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para otimizações."""
    query_lower = query.lower()
    
    product = extract_product_code(query)
    
    if "distribuir" in query_lower or "alocar" in query_lower:
        tool_name = "alocar_estoque_lojas"
        params = {}
        if product:
            params["produto_codigo"] = product
        reasoning = "Alocação inteligente de estoque"
        
    elif "transferência" in query_lower or "transferencia" in query_lower:
        tool_name = "sugerir_transferencias_automaticas"
        params = {}
        une = extract_une_filter(query)
        if une:
            params["une_origem"] = int(une)
        reasoning = "Sugestão de transferências automáticas"
        
    else:
        # Fallback
        tool_name = "alocar_estoque_lojas"
        params = {}
        if product:
            params["produto_codigo"] = product
        reasoning = "Otimização genérica (fallback para alocação)"
    
    return ToolSelection(
        tool_name=tool_name,
        tool_params=params,
        confidence=confidence * 0.9,
        fallback_tools=["consultar_dados_flexivel"],
        reasoning=reasoning
    )


def route_analysis(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para análises."""
    query_lower = query.lower()
    limit = extract_top_limit(query) or 20

    product = extract_product_code(query)
    une = extract_une_filter(query)

    # Casos de negócio comercial: ruptura deve priorizar ferramenta especializada.
    if re.search(r"ruptur\w*|falta\s+de\s+estoque|sem\s+estoque", query_lower):
        params: Dict[str, Any] = {"limite": limit}
        segment = extract_segment_filter(query)
        if segment:
            params["segmento"] = segment
        if une:
            params["une"] = une
        return ToolSelection(
            tool_name="encontrar_rupturas_criticas",
            tool_params=params,
            confidence=max(confidence, 0.90),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Análise de ruptura prioriza ferramenta especializada"
        )

    # Casos de queda/negatividade de vendas: direcionar para dados por grupo (sem depender de gráfico).
    if re.search(r"vend\w*\s+negativ\w*|vend\w*\s+ruin\w*|piores?\s+grupos?", query_lower):
        params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["NOMEGRUPO", "NOMESEGMENTO"],
            "ordenar_por": "valor",
            "ordem_desc": False,
            "limite": 200,
        }
        filtros = {}
        if une:
            filtros["UNE"] = int(une)
        segment = extract_segment_filter(query)
        if segment:
            filtros["NOMESEGMENTO"] = segment
        if filtros:
            params["filtros"] = filtros
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params=params,
            confidence=max(confidence, 0.88),
            fallback_tools=["gerar_grafico_universal_v2"],
            reasoning="Análise de vendas negativas/ruins por grupo com dados detalhados"
        )

    # Casos comerciais: "analise vendas ... grupos que precisam ação"
    if re.search(r"analis\w*\s+as?\s+vendas|grupos?\s+que\s+precisam\s+de\s+a[çc][aã]o", query_lower):
        params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["NOMEGRUPO", "NOMESEGMENTO"],
            "ordenar_por": "valor",
            "ordem_desc": False,  # menor venda primeiro = grupos prioritários para ação
            "limite": 120,
        }
        filtros = {}
        if une:
            filtros["UNE"] = int(une)
        segment = extract_segment_filter(query)
        if segment:
            filtros["NOMESEGMENTO"] = segment
        if filtros:
            params["filtros"] = filtros
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params=params,
            confidence=max(confidence, 0.90),
            fallback_tools=["gerar_grafico_universal_v2"],
            reasoning="Análise de grupos prioritários para ação com base em menor venda"
        )
    
    # Sub-classificação
    if product and ("todas as lojas" in query_lower or "toda a rede" in query_lower):
        tool_name = "analisar_produto_todas_lojas"
        params = {"produto_codigo": product}
        reasoning = "Análise de produto em toda a rede"
        
    elif "correlação" in query_lower or "correlacao" in query_lower:
        tool_name = "analise_correlacao_produtos"
        params = {}
        if product:
            params["produto_codigo"] = product
        reasoning = "Análise de correlação entre produtos"
        
    elif "histórico" in query_lower or "historico" in query_lower:
        tool_name = "analisar_historico_vendas"
        params = {}
        if product:
            params["produto_codigo"] = product
        days = extract_days_param(query)
        if days:
            params["dias_analise"] = days
        reasoning = "Análise de histórico de vendas"
        
    else:
        # Fallback para consulta flexível
        tool_name = "consultar_dados_flexivel"
        params = {"colunas": ["PRODUTO", "NOME", "VENDA_30DD", "ESTOQUE_UNE"]}
        if product:
            params["filtros"] = {"PRODUTO": product}
        if une:
            if "filtros" not in params:
                params["filtros"] = {}
            params["filtros"]["UNE"] = int(une)
        reasoning = "Análise genérica via consulta flexível"
    
    final_confidence = confidence * 0.85
    if tool_name == "consultar_dados_flexivel":
        final_confidence = max(final_confidence, 0.82)

    return ToolSelection(
        tool_name=tool_name,
        tool_params=params,
        confidence=final_confidence,
        fallback_tools=["consultar_dados_gerais"],
        reasoning=reasoning
    )


def route_data_query(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para consultas de dados."""
    query_lower = query.lower()
    if re.search(r"ruptur\w*|falta\s+de\s+estoque|sem\s+estoque", query_lower):
        return ToolSelection(
            tool_name="encontrar_rupturas_criticas",
            tool_params={"limite": extract_top_limit(query) or 20},
            confidence=max(confidence, 0.85),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Consulta textual de ruptura redirecionada para ferramenta específica"
        )

    if re.search(r"vend\w*\s+negativ\w*|vend\w*\s+ruin\w*|piores?\s+grupos?", query_lower):
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params={
                "agregacao": "SUM",
                "coluna_agregacao": "VENDA_30DD",
                "agrupar_por": ["NOMEGRUPO", "NOMESEGMENTO"],
                "ordenar_por": "valor",
                "ordem_desc": False,
                "limite": 200,
            },
            confidence=max(confidence, 0.84),
            fallback_tools=["gerar_grafico_universal_v2"],
            reasoning="Consulta de performance negativa redirecionada para análise de dados"
        )

    product = extract_product_code(query)
    une = extract_une_filter(query)
    segment = extract_segment_filter(query)
    
    params = {
        "colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"],
        "limite": "50"
    }
    
    filtros = {}
    if product:
        filtros["PRODUTO"] = product
    if une:
        filtros["UNE"] = int(une)
    if segment:
        filtros["NOMESEGMENTO"] = segment
    
    if filtros:
        params["filtros"] = filtros
    
    return ToolSelection(
        tool_name="consultar_dados_flexivel",
        tool_params=params,
        confidence=confidence,
        fallback_tools=["consultar_dados_gerais"],
        reasoning=f"Consulta de dados com filtros: {list(filtros.keys())}"
    )


def route_metadata(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para metadados."""
    return ToolSelection(
        tool_name="consultar_dicionario_dados",
        tool_params={},
        confidence=confidence,
        fallback_tools=[],
        reasoning="Consulta de schema/metadados"
    )


def route_query(intent: IntentType, query: str, confidence: float) -> ToolSelection:
    """
    Roteia query para ferramenta apropriada baseado na intenção.
    
    Args:
        intent: Tipo de intenção classificada
        query: Query original do usuário
        confidence: Confiança da classificação de intent
        
    Returns:
        ToolSelection com ferramenta, parâmetros e confiança
    """
    logger.info(f"[ROUTER] Routing {intent.value} with confidence {confidence:.2f}")
    
    # Dispatch para função específica
    routing_functions = {
        IntentType.VISUALIZATION: route_visualization,
        IntentType.FORECASTING: route_forecasting,
        IntentType.CALCULATION: route_calculation,
        IntentType.ANOMALY_DETECTION: route_anomaly_detection,
        IntentType.OPTIMIZATION: route_optimization,
        IntentType.ANALYSIS: route_analysis,
        IntentType.DATA_QUERY: route_data_query,
        IntentType.METADATA: route_metadata,
    }
    
    routing_func = routing_functions.get(intent)
    if not routing_func:
        logger.error(f"[ROUTER] No routing function for intent: {intent.value}")
        # Fallback absoluto
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params={"colunas": ["*"], "limite": 10},
            confidence=0.3,
            fallback_tools=[],
            reasoning="Fallback absoluto - intent desconhecido"
        )
    
    selection = routing_func(query, confidence)
    
    logger.info(
        f"[ROUTER] Selected: {selection.tool_name} "
        f"(confidence: {selection.confidence:.2f}, "
        f"params: {len(selection.tool_params)})"
    )
    
    return selection
