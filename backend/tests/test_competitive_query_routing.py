from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent


def test_is_competitive_query_detects_market_research_terms() -> None:
    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    assert agent._is_competitive_query("realize uma pesquisa de mercado do produto tnt branco") is True
    assert agent._is_competitive_query("quero benchmark de mercado para caneta azul") is True


def test_enrich_tool_selection_routes_market_research_to_competitive_tool() -> None:
    class ToolSelection:
        tool_name = "consultar_dados_flexivel"
        tool_params = {"colunas": ["PRODUTO"]}
        confidence = 0.51

    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    selection = ToolSelection()
    agent._enrich_tool_selection_for_business("realize uma pesquisa de mercado do produto tnt branco", selection)

    assert selection.tool_name == "pesquisar_precos_concorrentes"
    assert selection.tool_params.get("descricao_produto")
    assert selection.confidence >= 0.92
