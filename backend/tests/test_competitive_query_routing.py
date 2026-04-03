from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent


def test_is_competitive_query_detects_market_research_terms() -> None:
    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    assert agent._is_competitive_query("realize uma pesquisa de mercado do produto tnt branco") is True
    assert agent._is_competitive_query("quero benchmark de mercado para caneta azul") is True


def test_enrich_tool_selection_routes_generic_market_research_to_market_web() -> None:
    class ToolSelection:
        tool_name = "consultar_dados_flexivel"
        tool_params = {"colunas": ["PRODUTO"]}
        confidence = 0.51

    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    selection = ToolSelection()
    agent._enrich_tool_selection_for_business("realize uma pesquisa de mercado do produto tnt branco", selection)

    assert selection.tool_name == "pesquisar_mercado_web"
    assert selection.tool_params.get("termo_pesquisa") == "tnt branco"
    assert selection.confidence >= 0.92


def test_enrich_tool_selection_keeps_specific_competitor_on_competitive_tool() -> None:
    class ToolSelection:
        tool_name = "consultar_dados_flexivel"
        tool_params = {"colunas": ["PRODUTO"]}
        confidence = 0.51

    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    selection = ToolSelection()
    agent._enrich_tool_selection_for_business(
        "realize uma pesquisa de mercado do produto caneta bic na Kalunga",
        selection,
    )

    assert selection.tool_name == "pesquisar_precos_concorrentes"
    assert selection.tool_params.get("concorrentes") == "kalunga"
    assert selection.confidence >= 0.92
