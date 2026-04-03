"""
Query Router - Sistema de Roteamento Inteligente de Queries para Ferramentas
Mapeia intenção + contexto → ferramenta específica + parâmetros extraídos.

Author: Backend Specialist Agent
Date: 2026-01-24
"""

import re
import logging
from difflib import SequenceMatcher
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


def _normalize_query_for_extraction(query: str) -> str:
    """Normaliza typos recorrentes de palavras-chave de roteamento."""
    if not query:
        return query

    def normalize_segment_token(match: re.Match[str]) -> str:
        token = match.group(0)
        lower = token.lower()
        best_candidate = token
        best_ratio = 0.0
        for candidate in ("segmento", "segmentos"):
            ratio = SequenceMatcher(None, lower, candidate).ratio()
            if ratio > best_ratio:
                best_candidate = candidate
                best_ratio = ratio
        if best_ratio >= 0.78:
            return best_candidate
        return token

    return re.sub(
        r"\b[\wÀ-ÿ-]{6,12}\b",
        normalize_segment_token,
        query,
        flags=re.IGNORECASE,
    )


def extract_une_filter(query: str) -> Optional[str]:
    """Extrai identificador de UNE da query, aceitando códigos numéricos e textuais."""
    if not query:
        return None

    patterns = [
        r"\bu+ne\s+([a-z0-9][a-z0-9_-]{0,11})\b",  # tolera typo: uune, uuune...
        r"\bune\s+([a-z0-9][a-z0-9_-]{0,11})\b",
        r"\bloja\s+([a-z0-9][a-z0-9_-]{0,11})\b",
        r"\bunidade\s+([a-z0-9][a-z0-9_-]{0,11})\b",
        r"\b(?:na|no|da|do)\s+une\s+([a-z0-9][a-z0-9_-]{0,11})\b",
        r"\b(?:na|no|da|do)\s+loja\s+([a-z0-9][a-z0-9_-]{0,11})\b",
        r"\b(?:na|no|da|do)\s+([a-z]{2,10}[a-z0-9_-]{0,8})\b",
        r"\b(?:na|da)\s+(\d{3,4})\b",
    ]
    blocked_tokens = {
        "toda", "todas", "todo", "todos",
        "une", "unes", "loja", "lojas", "unidade", "unidades",
        "rede", "grupo", "segmento", "segmentos",
        "categoria", "categorias",
    }

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if not match:
            continue
        une = str(match.group(1) or "").strip()
        if not une:
            continue
        if une.lower() in blocked_tokens:
            continue
        logger.debug(f"[ROUTER] Extracted UNE: {une}")
        return une.upper() if any(ch.isalpha() for ch in une) else une

    return None


def _is_numeric_une(une: Optional[str]) -> bool:
    return bool(str(une or "").isdigit())


def _coerce_une_filter_value(une: Optional[str]) -> Optional[Any]:
    if une in (None, "", []):
        return None
    return int(str(une)) if _is_numeric_une(une) else str(une)


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
    if not query:
        return None

    normalized_query = _normalize_query_for_extraction(query)

    # Captura segmento multi-palavra e remove sufixos de escopo (ex.: "de todas as unes").
    patterns = [
        r"(?:d[oa]|de)?\s*segmento\s+([a-zA-ZÀ-ÿ0-9 _-]+?)(?:\s+em\s+|\s+na\s+|\s+no\s+|\s+nos?\s+|\s+nas?\s+|\s+por\s+|\s+com\s+|\s+para\s+|$)",
        r"\bsegmento\s+([a-zA-ZÀ-ÿ0-9 _-]+)$",
    ]
    trailing_scope_patterns = [
        r"\s+(?:de|em|na|no)\s+t[oó]d?as?\s+as?\s+(?:unes?|lojas?)\b.*$",
        r"\s+t[oó]d?as?\s+as?\s+(?:unes?|lojas?)\b.*$",
        r"\s+toda\s+a\s+rede\b.*$",
        r"\s+(?:na|no|une|loja)\s+\d{3,4}\b.*$",
        r"\s+por\s+(?:une|unes|loja|lojas|unidade)\b.*$",
        r"\s+de\s+cada\s+(?:une|unes|loja|lojas|unidade)\b.*$",
        r"\s+com\s+kpis?\b.*$",
        r"\s+(?:para\s+os?|nos?|das?|dos?)\s+[uú]ltim[oa]s?\s+\d+\s+(?:dias|semanas?|meses?)\b.*$",
        r"\s+(?:neste|nesta|no|na|do|da)\s+(?:m[eê]s|dia)\s+atual\b.*$",
    ]
    invalid_segment_tokens = {
        "a", "as", "o", "os",
        "da", "das", "de", "do", "dos",
        "em", "na", "nas", "no", "nos",
        "para", "por", "com",
    }

    for pattern in patterns:
        match = re.search(pattern, normalized_query, re.IGNORECASE)
        if not match:
            continue

        segment = re.sub(r"\s+", " ", match.group(1).strip(" .,:;!?-"))
        for trailing in trailing_scope_patterns:
            segment = re.sub(trailing, "", segment, flags=re.IGNORECASE).strip(" .,:;!?-")

        if not segment:
            continue

        # Evita capturar apenas termos de escopo (une/loja/rede).
        segment_lower = segment.lower()
        if segment_lower in invalid_segment_tokens or len(segment_lower) <= 2:
            continue
        if re.fullmatch(r"(?:une|unes|loja|lojas|rede)(?:\s+\w+)?", segment_lower):
            continue

        segment = segment.upper()
        logger.debug(f"[ROUTER] Extracted segment: {segment}")
        return segment

    return None


def is_all_stores_scope(query: str) -> bool:
    """Detecta menções a toda a rede, com tolerância a pequenos typos."""
    if not query:
        return False
    q = query.lower()
    return bool(
        re.search(r"\bt[oó]d?as?\s+as?\s+(?:unes?|lojas?)\b", q)
        or re.search(r"\bem\s+t[oó]d?as?\s+as?\s+(?:unes?|lojas?)\b", q)
        or re.search(r"\btoda\s+a\s+rede\b", q)
        or re.search(r"\bem\s+toda\s+a\s+rede\b", q)
    )


def extract_top_limit(query: str) -> Optional[int]:
    """Extrai limite de top N da query."""
    # Padrões: "top 10", "5 maiores", "3 principais"
    patterns = [
        r"top\s+(\d+)",
        r"(\d+)\s+maiores",
        r"(\d+)\s+menores",
        r"(\d+)\s+principais",
        r"quais?\s+(\d+)\s+lojas?\b",
        r"(\d+)\s+lojas?\s+mais\s+v\w+",
        r"(\d+)\s+lojas?\s+menos\s+v\w+",
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


def extract_percentage_param(query: str) -> Optional[float]:
    """Extrai percentual da query."""
    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*%",
        r"desconto\s+de\s+(\d+(?:[.,]\d+)?)",
        r"promo[çc][aã]o\s+de\s+(\d+(?:[.,]\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", "."))

    return None


def extract_ranking_param(query: str) -> Optional[int]:
    """Extrai ranking comercial da query para política de preço."""
    if not query:
        return None
    patterns = [
        r"ranking\s+(\d)",
        r"classifica(?:ç|c)[aã]o\s+(\d)",
        r"faixa\s+(\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_payment_term(query: str) -> Optional[str]:
    """Extrai forma de pagamento da query."""
    if not query:
        return None
    q = query.lower()
    if "à vista" in q or "a vista" in q or "avista" in q or "vista" in q:
        return "vista"
    for term in ("30d", "90d", "120d"):
        if term in q:
            return term
    return None


def extract_purchase_value(query: str) -> Optional[float]:
    """Extrai valor de compra/orçamento da query."""
    if not query:
        return None
    patterns = [
        r"valor\s+(?:de\s+compra\s+)?(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
        r"compra\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
        r"pedido\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
        r"or[çc]amento\s+(?:de\s+)?r?\$?\s*(\d+(?:[.,]\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def is_market_basket_query(query: str) -> bool:
    """Detecta perguntas sobre itens que saem juntos / market basket."""
    q = (query or "").lower()
    markers = [
        "vendem juntos",
        "saem juntos",
        "comprados juntos",
        "itens associados",
        "market basket",
        "afinidade entre produtos",
    ]
    return any(marker in q for marker in markers)


def infer_segment_from_keywords(query: str) -> Optional[str]:
    q = (query or "").lower()
    keyword_map = {
        "PAPELARIA": ["papelaria", "volta às aulas", "volta as aulas", "material escolar"],
        "ARTES": ["artesanato", "artes", "eva", "brush pen", "tela", "pintura"],
        "ARMARINHO": ["armarinho", "aviamento", "costura", "linhas", "botões", "botoes"],
    }
    for segment, markers in keyword_map.items():
        if any(marker in q for marker in markers):
            return segment
    return None


def extract_period_filter(query: str) -> Optional[str]:
    """Extrai recorte temporal para dashboards/visualizações."""
    if not query:
        return None

    q = query.lower()
    patterns: List[Tuple[str, str]] = [
        (r"[uú]ltimos?\s+(\d+)\s+dias", "d"),
        (r"[uú]ltimas?\s+(\d+)\s+semanas?", "w"),
        (r"[uú]ltimos?\s+(\d+)\s+meses?", "m"),
    ]

    for pattern, suffix in patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            return f"{int(match.group(1))}{suffix}"

    if re.search(r"\b(m[eê]s atual|este m[eê]s)\b", q):
        return "mes_atual"

    if re.search(r"\b(hoje|dia atual)\b", q):
        return "hoje"

    return None


def is_product_store_leader_query(query: str) -> bool:
    """Detecta perguntas do tipo 'qual loja mais vende o produto X?'."""
    if not query:
        return False

    q = _normalize_query_for_extraction(query).lower()
    if extract_product_code(query) is None:
        return False
    explicit_limit = extract_top_limit(query)
    if (explicit_limit and explicit_limit > 1) or "quais lojas" in q or "ranking" in q or "top " in q:
        return False

    comparative_store_patterns = [
        r"\bqual(?:\s+é|\s+e)?\s+(?:a\s+)?loja\s+mais\s+v(?:end|ed)\w*",
        r"\bem\s+qual\s+loja\b.*\bv(?:end|ed)\w*",
        r"\bloja\s+l[íi]der\b",
        r"\bmais\s+v(?:end|ed)\w*\s+o\s+produto\b",
    ]

    return any(re.search(pattern, q, re.IGNORECASE) for pattern in comparative_store_patterns)


def extract_product_store_ranking_request(query: str) -> Optional[Dict[str, Any]]:
    """Extrai intenção de ranking de lojas para um produto específico."""
    if not query:
        return None

    q = _normalize_query_for_extraction(query).lower()
    if extract_product_code(query) is None:
        return None

    highest_patterns = [
        r"\bquais?\s+\d+\s+lojas?\s+mais\s+v(?:end|ed)\w*",
        r"\bquais?\s+lojas?\s+mais\s+v(?:end|ed)\w*",
        r"\btop\s+\d+\s+lojas\b",
        r"\branking\s+das?\s+lojas\b",
        r"\blojas?\s+com\s+maior(?:es)?\s+vendas?\b",
        r"\bmais\s+v(?:end|ed)\w*\s+o\s+produto\b",
    ]
    lowest_patterns = [
        r"\bqual(?:\s+é|\s+e)?\s+(?:a\s+)?loja\s+menos\s+v\w*",
        r"\bquais?\s+\d+\s+lojas?\s+menos\s+v\w*",
        r"\bquais?\s+lojas?\s+menos\s+v\w*",
        r"\blojas?\s+com\s+menor(?:es)?\s+vendas?\b",
        r"\bvende\s+menos\s+o\s+produto\b",
        r"\bmenos\s+v\w*\s+o\s+produto\b",
    ]

    if any(re.search(pattern, q, re.IGNORECASE) for pattern in lowest_patterns):
        return {"ordem_desc": False, "limite": extract_top_limit(query) or 1}

    if any(re.search(pattern, q, re.IGNORECASE) for pattern in highest_patterns):
        return {"ordem_desc": True, "limite": extract_top_limit(query) or 5}

    return None


def is_product_rupture_query(query: str) -> bool:
    """Detecta perguntas sobre ruptura/falta de estoque para um produto específico."""
    if not query:
        return False

    q = _normalize_query_for_extraction(query).lower()
    if extract_product_code(query) is None:
        return False

    rupture_markers = [
        r"ruptur\w*",
        r"falta\s+de\s+estoque",
        r"sem\s+estoque",
        r"em\s+ruptura",
    ]
    return any(re.search(pattern, q, re.IGNORECASE) for pattern in rupture_markers)


def extract_chart_breakdown(query: str) -> Optional[str]:
    """Infere dimensão principal do gráfico a partir da pergunta."""
    if not query:
        return None
    q = _normalize_query_for_extraction(query).lower()
    segment_filter = extract_segment_filter(query)

    explicit_store_breakdown_patterns = [
        r"\b(?:tabela|ranking|gr[aá]fico|grafico)\s+por\s+(?:une|loja|unidade)\b",
        r"\bpor\s+(?:une|loja|unidade)\b",
        r"\bcada\s+(?:une|loja|unidade)\b",
        r"\branking\s+d[aeo]s?\s+(?:unes?|lojas?)\b",
        r"\b(?:unes?|lojas?)\s+de\s+(?:menor|maior)\s+venda\b",
        r"\bcompar(?:e|ar|ação|acao)?\s+(?:entre\s+)?(?:unes?|lojas?)\b",
    ]
    if is_product_store_leader_query(query) or any(
        re.search(pattern, q, re.IGNORECASE) for pattern in explicit_store_breakdown_patterns
    ):
        return "LOJA"

    # Se o segmento já virou filtro explícito e a pergunta pede toda a rede,
    # o eixo esperado deixa de ser "segmento" e passa a ser "loja/UNE".
    if segment_filter and is_all_stores_scope(query):
        return "LOJA"

    # "em todas as UNEs/lojas" define escopo, não eixo do gráfico.
    if re.search(r"\bsegmentos?\b", q, re.IGNORECASE):
        return "SEGMENTO"
    if re.search(r"\bcategorias?\b", q, re.IGNORECASE):
        return "CATEGORIA"
    if re.search(r"\bgrupos?\b", q, re.IGNORECASE):
        return "GRUPO"
    if re.search(r"\b(?:produto|produtos|sku|item|itens)\b", q, re.IGNORECASE):
        return "PRODUTO"
    if re.search(r"\b(?:fabricante|marca)\b", q, re.IGNORECASE):
        return "FABRICANTE"

    # Fallback: só assume loja quando a consulta fala de UNE/loja como objeto principal,
    # não como filtro de escopo ("na UNE 520", "em todas as UNEs", etc.).
    if re.search(r"\b(?:vendas?|estoque|ranking|desempenho)\s+das?\s+(?:unes?|lojas?)\b", q, re.IGNORECASE):
        return "LOJA"
    if re.search(r"\b(?:unes?|lojas?)\b", q, re.IGNORECASE) and not is_all_stores_scope(query):
        return "LOJA"
    return None


def is_explicit_table_request(query: str) -> bool:
    """Detecta quando o usuário quer uma saída tabular explícita."""
    if not query:
        return False
    q = _normalize_query_for_extraction(query).lower()
    markers = (
        "tabela",
        "tabular",
        "mostre em tabela",
        "lista em tabela",
        "me mostre em tabela",
    )
    return any(marker in q for marker in markers)


def map_breakdown_to_group_column(breakdown: Optional[str]) -> Optional[str]:
    if not breakdown:
        return None
    mapping = {
        "LOJA": "UNE",
        "SEGMENTO": "NOMESEGMENTO",
        "CATEGORIA": "NOMECATEGORIA",
        "GRUPO": "NOMEGRUPO",
        "FABRICANTE": "NOMEFABRICANTE",
        "PRODUTO": "PRODUTO",
    }
    return mapping.get(str(breakdown).upper())


def route_visualization(query: str, confidence: float) -> ToolSelection:
    """Roteamento específico para visualizações."""
    query_lower = query.lower()
    
    # Sub-classificação
    if "dashboard" in query_lower:
        params: Dict[str, Any] = {}
        segment = extract_segment_filter(query)
        une = extract_une_filter(query)
        period = extract_period_filter(query)
        if segment:
            params["segmento"] = segment
        if une:
            params["une"] = une
        if period:
            params["periodo"] = period
        if is_all_stores_scope(query):
            params["escopo"] = "rede"

        return ToolSelection(
            tool_name="gerar_dashboard_executivo",
            tool_params=params,
            confidence=confidence * 0.95,
            fallback_tools=["gerar_grafico_universal_v2", "consultar_dados_flexivel"],
            reasoning=f"Dashboard executivo detectado com filtros: {list(params.keys())}"
        )
    
    # Default: gerar_grafico_universal_v2 (ferramenta universal)
    params = {
        "descricao": query,
        "tipo_grafico": "auto"
    }
    breakdown = extract_chart_breakdown(query)
    if breakdown:
        params["quebra_por"] = breakdown
    
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
        tool_name = "prever_demanda"
        reasoning = "Previsão com sazonalidade detectada"
    elif "tendência" in query_lower or "regressão" in query_lower:
        tool_name = "analise_regressao_vendas"
        reasoning = "Análise de tendência via regressão"
    else:
        tool_name = "prever_demanda"  # Default
        reasoning = "Previsão de demanda padrão"
    
    params = {}
    if product:
        params["produto_id"] = str(product)
    if tool_name == "prever_demanda":
        params["periodo_dias"] = days
    elif tool_name == "analise_regressao_vendas":
        params["periodo_dias"] = days
    
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
    desconto_pct = extract_percentage_param(query)
    ranking = extract_ranking_param(query)
    payment_term = extract_payment_term(query)
    purchase_value = extract_purchase_value(query)
    cart_context = any(
        marker in query_lower
        for marker in ["cesta", "carrinho", "pedido", "combo", "basket"]
    )
    promotion_context = any(
        marker in query_lower
        for marker in ["promo", "desconto", "oferta", "campanha"]
    )
    margin_context = any(
        marker in query_lower
        for marker in ["margem", "rentabilidade", "lucro"]
    )
    inferred_segment = extract_segment_filter(query) or infer_segment_from_keywords(query)
    has_explicit_item_payload = bool(
        product
        or re.search(r"\bsku\s+\d+\b", query_lower)
        or re.search(r"\bproduto\s+\d+\b", query_lower)
        or any(token in query for token in ['{"', "[{", '"itens"', "'itens'"])
    )

    # Sub-classificação de cálculo
    if is_market_basket_query(query):
        tool_name = "minerar_cestas_frequentes"
        params = {}
        reasoning = "Pergunta sobre itens que saem juntos deve usar market basket dedicado"
    elif cart_context and not has_explicit_item_payload:
        tool_name = "consultar_dados_flexivel"
        params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["PRODUTO", "NOME", "NOMESEGMENTO"],
            "ordenar_por": "valor",
            "ordem_desc": True,
            "limite": "12",
        }
        if inferred_segment:
            params["filtros"] = {"NOMESEGMENTO": inferred_segment}
        reasoning = "Pergunta de cesta/combo sem payload transacional; usando mix real de produtos por venda"
    elif cart_context and promotion_context:
        params = {}
        if desconto_pct is not None:
            params["desconto_pct"] = desconto_pct
        tool_name = "simular_promocao_cesta"
        reasoning = "Simulação de impacto promocional em cesta/carrinho"
    elif cart_context and margin_context:
        tool_name = "analisar_cesta_compras"
        params = {}
        reasoning = "Cálculo determinístico de margem real da cesta"
    elif cart_context:
        tool_name = "analisar_cesta_compras"
        params = {}
        reasoning = "Análise completa de cesta/carrinho"
    elif "eoq" in query_lower or "lote econômico" in query_lower or "quanto comprar" in query_lower:
        tool_name = "calcular_eoq"
        params = {"produto_id": str(product)} if product else {}
        if product:
            params["produto_id"] = str(product)
        reasoning = "Cálculo de EOQ (lote econômico)"
        
    elif "media comum" in query_lower or "média comum" in query_lower or "mc de estoque" in query_lower:
        if product and une and _is_numeric_une(une):
            tool_name = "calcular_mc_produto"
            params = {"produto_id": int(product), "une_id": int(une)}
            reasoning = "Cálculo de média comum para estoque"
        else:
            tool_name = "consultar_dados_flexivel"
            params = {"colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"], "limite": "50"}
            filtros = {}
            if product:
                filtros["PRODUTO"] = product
            if une:
                filtros["UNE"] = _coerce_une_filter_value(une)
            if filtros:
                params["filtros"] = filtros
            reasoning = "Média comum solicitada sem parâmetros mínimos; fallback para dados base"
    elif ("margem de contribuição" in query_lower or "media comum" in query_lower or "média comum" in query_lower or re.search(r"\bmc\b", query_lower)) and product and une and _is_numeric_une(une):
        tool_name = "calcular_mc_produto"
        params = {"produto_id": int(product), "une_id": int(une)}
        reasoning = "Consulta de MC/Média Comum diretamente na UNE informada"
    elif "margem" in query_lower or "mc" in query_lower:
        tool_name = "consultar_dados_flexivel"
        params = {
            "colunas": ["PRODUTO", "NOME", "UNE", "LIQUIDO_38", "ULTIMA_ENTRADA_CUSTO_CD", "VENDA_30DD", "ESTOQUE_UNE", "ESTOQUE_CD", "MEDIA_CONSIDERADA_LV"],
            "limite": "50",
        }
        filtros = {}
        if product:
            filtros["PRODUTO"] = product
        if une:
            filtros["UNE"] = _coerce_une_filter_value(une)
        if filtros:
            params["filtros"] = filtros
        reasoning = "Margem solicitada sem semântica de cesta; retorno dos dados de preço e custo para análise correta"
        
    elif "preço final" in query_lower or "preco final" in query_lower:
        if purchase_value is not None and ranking is not None and payment_term:
            tool_name = "calcular_preco_final_une"
            params = {
                "valor_compra": purchase_value,
                "ranking": ranking,
                "forma_pagamento": payment_term,
            }
            reasoning = "Preço final com política comercial calculado por parâmetros explícitos"
        else:
            tool_name = "consultar_dados_flexivel"
            params = {"colunas": ["PRODUTO", "NOME", "LIQUIDO_38", "ULTIMA_ENTRADA_CUSTO_CD"], "limite": "50"}
            if product:
                params["filtros"] = {"PRODUTO": product}
            reasoning = "Preço final solicitado sem parâmetros completos; fallback para dados de preço e custo"
    elif any(marker in query_lower for marker in ["markup", "mark-up", "giro", "cobertura"]):
        tool_name = "consultar_dados_flexivel"
        params = {
            "colunas": ["PRODUTO", "NOME", "UNE", "LIQUIDO_38", "ULTIMA_ENTRADA_CUSTO_CD", "VENDA_30DD", "ESTOQUE_UNE", "ESTOQUE_CD", "MEDIA_CONSIDERADA_LV"],
            "limite": "50",
        }
        filtros = {}
        if product:
            filtros["PRODUTO"] = product
        if une:
            filtros["UNE"] = _coerce_une_filter_value(une)
        if filtros:
            params["filtros"] = filtros
        reasoning = "Cálculo operacional de markup, giro ou cobertura com base em preço, custo, venda e estoque"
        
    else:
        # Fallback genérico
        tool_name = "calcular_eoq" if product else "consultar_dados_flexivel"
        params = {"produto_id": str(product)} if product else {"colunas": ["PRODUTO", "NOME", "VENDA_30DD"], "limite": "20"}
        if product:
            params["produto_id"] = str(product)
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
        "periodo_dias": days,
        "sensibilidade": 2.5  # Default moderado
    }
    
    if product:
        params["produto_id"] = str(product)
    
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
    
    qty_match = re.search(r"(\d+)\s*(?:unidades|itens|pe[cç]as|unid)\b", query_lower)
    quantidade_total = int(qty_match.group(1)) if qty_match else None

    if "distribuir" in query_lower or "alocar" in query_lower:
        if product and quantidade_total:
            tool_name = "alocar_estoque_lojas"
            params = {"produto_id": str(product), "quantidade_total": quantidade_total}
            reasoning = "Alocação inteligente de estoque"
        else:
            # Sem quantidade explícita, usar ferramenta mais robusta para diagnóstico operacional.
            tool_name = "consultar_dados_flexivel"
            params = {"colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"], "limite": "100"}
            if product:
                params["filtros"] = {"PRODUTO": product}
            reasoning = "Solicitação de alocação sem quantidade total; fallback para diagnóstico de estoque por loja"
        
    elif "transferência" in query_lower or "transferencia" in query_lower:
        tool_name = "sugerir_transferencias_automaticas"
        params = {}
        une = extract_une_filter(query)
        if une and _is_numeric_une(une):
            params["une_origem_filtro"] = int(une)
        reasoning = "Sugestão de transferências automáticas"
        
    else:
        # Fallback seguro: evita chamar alocação sem parâmetros obrigatórios.
        tool_name = "consultar_dados_flexivel"
        params = {"colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"], "limite": "100"}
        if product:
            params["filtros"] = {"PRODUTO": product}
        reasoning = "Otimização genérica com diagnóstico de estoque (fallback seguro)"
    
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
    segment = extract_segment_filter(query) or infer_segment_from_keywords(query)
    store_ranking = extract_product_store_ranking_request(query)
    product_rupture = is_product_rupture_query(query)

    if re.search(r"\bcompare?\b|\bcomparativo\b|\bversus\b|\bvs\.?\b", query_lower):
        breakdown = extract_chart_breakdown(query) or "LOJA"
        breakdown_map = {
            "LOJA": ["UNE"],
            "SEGMENTO": ["NOMESEGMENTO"],
            "CATEGORIA": ["NOMECATEGORIA"],
            "GRUPO": ["NOMEGRUPO"],
            "PRODUTO": ["PRODUTO", "NOME"],
        }
        params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": breakdown_map.get(breakdown, ["UNE"]),
            "ordenar_por": "valor",
            "ordem_desc": True,
            "limite": 50,
        }
        filtros: Dict[str, Any] = {}
        if product and breakdown != "PRODUTO":
            filtros["PRODUTO"] = product
        if une and breakdown != "LOJA":
            filtros["UNE"] = _coerce_une_filter_value(une)
        if segment and breakdown != "SEGMENTO":
            filtros["NOMESEGMENTO"] = segment
        if filtros:
            params["filtros"] = filtros
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params=params,
            confidence=max(confidence, 0.90),
            fallback_tools=["gerar_grafico_universal_v2"],
            reasoning="Comparação analítica sem pedido explícito de gráfico; priorizando tabela/dados",
        )

    if any(token in query_lower for token in ["combo", "cross-sell", "cross sell", "ticket medio", "ticket médio", "volta às aulas", "volta as aulas"]):
        params = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["PRODUTO", "NOME", "NOMESEGMENTO"],
            "ordenar_por": "valor",
            "ordem_desc": True,
            "limite": 12,
        }
        if segment:
            params["filtros"] = {"NOMESEGMENTO": segment}
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params=params,
            confidence=max(confidence, 0.88),
            fallback_tools=[],
            reasoning="Sugestão de combo/cross-sell baseada em giro real do mix interno",
        )

    if is_market_basket_query(query):
        return ToolSelection(
            tool_name="minerar_cestas_frequentes",
            tool_params={},
            confidence=max(confidence, 0.90),
            fallback_tools=["analise_correlacao_produtos"],
            reasoning="Pergunta sobre itens que saem juntos deve usar market basket dedicado",
        )

    if product and product_rupture:
        return ToolSelection(
            tool_name="analisar_produto_todas_lojas",
            tool_params={"produto_codigo": product},
            confidence=max(confidence, 0.91),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Ruptura de produto específico deve usar análise multi-loja com lista de lojas em ruptura",
        )

    if product and is_product_store_leader_query(query):
        return ToolSelection(
            tool_name="analisar_produto_todas_lojas",
            tool_params={"produto_codigo": product},
            confidence=max(confidence, 0.88),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Pergunta comparativa por loja para produto específico; usando análise multi-loja",
        )
    if product and store_ranking:
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params={
                "agregacao": "SUM",
                "coluna_agregacao": "VENDA_30DD",
                "agrupar_por": ["UNE"],
                "ordenar_por": "valor",
                "ordem_desc": bool(store_ranking["ordem_desc"]),
                "limite": int(store_ranking["limite"]),
                "filtros": {"PRODUTO": product},
            },
            confidence=max(confidence, 0.89),
            fallback_tools=["consultar_dados_gerais"],
            reasoning="Ranking de lojas para produto específico com agregação por UNE",
        )

    # Casos de negócio comercial: ruptura deve priorizar ferramenta especializada.
    if re.search(r"ruptur\w*|falta\s+de\s+estoque|sem\s+estoque", query_lower):
        params: Dict[str, Any] = {"limite": limit}
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
            filtros["UNE"] = _coerce_une_filter_value(une)
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
            filtros["UNE"] = _coerce_une_filter_value(une)
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
    if product and is_all_stores_scope(query):
        tool_name = "analisar_produto_todas_lojas"
        params = {"produto_codigo": product}
        reasoning = "Análise de produto em toda a rede"
        
    elif "correlação" in query_lower or "correlacao" in query_lower:
        tool_name = "analise_correlacao_produtos"
        params = {}
        if product:
            params["produtos_ids"] = [str(product)]
        reasoning = "Análise de correlação entre produtos"
        
    elif "histórico" in query_lower or "historico" in query_lower:
        tool_name = "analisar_historico_vendas" if not une or _is_numeric_une(une) else "consultar_dados_flexivel"
        params = {}
        if product:
            if tool_name == "analisar_historico_vendas":
                params["codigo_produto"] = int(product)
            else:
                params.setdefault("filtros", {})["PRODUTO"] = product
        if une:
            if tool_name == "analisar_historico_vendas":
                params["codigo_une"] = int(une)
            else:
                params.setdefault("filtros", {})["UNE"] = _coerce_une_filter_value(une)
        if segment and tool_name == "consultar_dados_flexivel":
            params.setdefault("filtros", {})["NOMESEGMENTO"] = segment
        if tool_name == "consultar_dados_flexivel":
            params.setdefault("colunas", ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"])
            params.setdefault("limite", "50")
            reasoning = "Histórico com UNE textual; fallback para consulta flexível com filtro de UNE"
        else:
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
            params["filtros"]["UNE"] = _coerce_une_filter_value(une)
        if segment:
            if "filtros" not in params:
                params["filtros"] = {}
            params["filtros"]["NOMESEGMENTO"] = segment
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
    product = extract_product_code(query)
    if product and is_product_rupture_query(query):
        return ToolSelection(
            tool_name="analisar_produto_todas_lojas",
            tool_params={"produto_codigo": product},
            confidence=max(confidence, 0.91),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Consulta de ruptura para produto específico redirecionada para análise multi-loja",
        )

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

    une = extract_une_filter(query)
    segment = extract_segment_filter(query)
    store_ranking = extract_product_store_ranking_request(query)
    breakdown = extract_chart_breakdown(query)
    group_column = map_breakdown_to_group_column(breakdown)

    if is_explicit_table_request(query) and group_column:
        params: Dict[str, Any] = {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": [group_column],
            "ordenar_por": "valor",
            "ordem_desc": True,
            "limite": extract_top_limit(query) or 50,
        }
        filtros = {}
        if product and group_column != "PRODUTO":
            filtros["PRODUTO"] = product
        if une and group_column != "UNE":
            filtros["UNE"] = _coerce_une_filter_value(une)
        if segment and group_column != "NOMESEGMENTO":
            filtros["NOMESEGMENTO"] = segment
        if filtros:
            params["filtros"] = filtros

        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params=params,
            confidence=max(confidence, 0.87),
            fallback_tools=["consultar_dados_gerais"],
            reasoning=f"Consulta tabular agregada por {group_column}",
        )

    if product and is_product_store_leader_query(query):
        return ToolSelection(
            tool_name="analisar_produto_todas_lojas",
            tool_params={"produto_codigo": product},
            confidence=max(confidence, 0.88),
            fallback_tools=["consultar_dados_flexivel"],
            reasoning="Consulta de loja líder para produto específico redirecionada para análise multi-loja",
        )
    if product and store_ranking:
        return ToolSelection(
            tool_name="consultar_dados_flexivel",
            tool_params={
                "agregacao": "SUM",
                "coluna_agregacao": "VENDA_30DD",
                "agrupar_por": ["UNE"],
                "ordenar_por": "valor",
                "ordem_desc": bool(store_ranking["ordem_desc"]),
                "limite": int(store_ranking["limite"]),
                "filtros": {"PRODUTO": product},
            },
            confidence=max(confidence, 0.89),
            fallback_tools=["consultar_dados_gerais"],
            reasoning="Consulta de ranking de lojas para produto específico com agregação por UNE",
        )
    
    params = {
        "colunas": ["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE"],
        "limite": "50"
    }
    
    filtros = {}
    if product:
        filtros["PRODUTO"] = product
    if une:
        filtros["UNE"] = _coerce_une_filter_value(une)
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
