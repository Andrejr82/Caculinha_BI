"""
Testes de integração de roteamento/escopo das tools do ChatBI.
Garante compatibilidade entre nomes/parâmetros roteados e ferramentas disponíveis por role.
"""

from backend.app.core.utils.intent_classifier import classify_intent
from backend.app.core.utils.query_router import route_query
from backend.app.core.utils.tool_scoping import ToolPermissionManager


def test_forecasting_route_uses_real_tool_signature() -> None:
    query = "qual a previsão de vendas do produto 25 para os próximos 30 dias?"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "prever_demanda"
    assert selection.tool_params.get("produto_id") == "25"
    assert selection.tool_params.get("periodo_dias") == 30


def test_calculation_route_uses_real_tool_signature() -> None:
    query = "calcule o lote econômico para o produto 369947"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "calcular_eoq"
    assert selection.tool_params.get("produto_id") == "369947"


def test_calculation_route_uses_basket_margin_tool() -> None:
    query = "calcule a margem real desta cesta de compras com frete e impostos"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "analisar_cesta_compras"


def test_calculation_route_uses_promotion_simulator() -> None:
    query = "simule o impacto de 10% de desconto na cesta"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "simular_promocao_cesta"
    assert selection.tool_params.get("desconto_pct") == 10.0


def test_optimization_transfer_param_matches_tool() -> None:
    query = "sugerir transferência da une 1685"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "sugerir_transferencias_automaticas"
    assert selection.tool_params.get("une_origem_filtro") == 1685


def test_analysis_product_all_stores_route_is_supported() -> None:
    query = "analise o produto 25 em todas as lojas"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "analisar_produto_todas_lojas"
    assert selection.tool_params.get("produto_codigo") == 25


def test_analysis_route_uses_market_basket_tool() -> None:
    query = "quais produtos saem juntos na cesta de compras"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "minerar_cestas_frequentes"


def test_dashboard_route_with_segment_is_supported() -> None:
    query = "gere um dashboard interativo do segmento artes nos ultimos 30 dias"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "gerar_dashboard_executivo"
    assert selection.tool_params.get("segmento") == "ARTES"
    assert selection.tool_params.get("periodo") == "30d"


def test_all_primary_routes_are_allowed_for_analyst() -> None:
    allowed = set(ToolPermissionManager.list_available_tools("analyst"))
    # Cobertura de intenções principais do ChatBI.
    queries = [
        "gere um gráfico de vendas por segmento",
        "qual a previsão de vendas do produto 25 para os próximos 30 dias?",
        "calcule o lote econômico para o produto 369947",
        "calcule a margem real desta cesta de compras",
        "simule o impacto de 10% de desconto na cesta",
        "detecte vendas anormais do produto 369947",
        "sugerir transferência da une 1685",
        "analise o produto 25 em todas as lojas",
        "quais produtos saem juntos na cesta de compras?",
        "quais colunas existem no banco?",
        "quantos produtos temos cadastrados?",
    ]

    for query in queries:
        intent = classify_intent(query)
        selection = route_query(intent.intent, query, intent.confidence)
        assert selection.tool_name in allowed, f"Tool fora do escopo analyst: {selection.tool_name} | query={query}"


def test_visualization_route_infers_segment_breakdown() -> None:
    query = "gere um gráfico de vendas por segmento nos últimos 90 dias"
    intent = classify_intent(query)
    selection = route_query(intent.intent, query, intent.confidence)

    assert selection.tool_name == "gerar_grafico_universal_v2"
    assert selection.tool_params.get("quebra_por") == "SEGMENTO"
