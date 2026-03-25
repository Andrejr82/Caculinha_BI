import time
from types import SimpleNamespace

import pytest

from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.utils.intent_classifier import IntentType, classify_intent


def _agent_stub() -> CaculinhaBIAgent:
    return CaculinhaBIAgent.__new__(CaculinhaBIAgent)


def test_intent_classifier_detects_commercial_plan_as_analysis():
    result = classify_intent("me de um plano comercial para 7 dias")
    assert result.intent == IntentType.ANALYSIS
    assert result.confidence >= 0.8


def test_intent_classifier_detects_contextual_action_followup_as_analysis():
    result = classify_intent("com base na última resposta, quais ações você recomenda?")
    assert result.intent == IntentType.ANALYSIS
    assert result.confidence >= 0.8


def test_intent_classifier_handles_partial_relatorio_token():
    result = classify_intent("preciso de um relatorio de vendas do produto 369947")
    assert result.intent == IntentType.ANALYSIS


def test_intent_classifier_handles_typo_relatorio_token():
    result = classify_intent("preciso de um rela´rptio de vendas do produto 369947 em todas as lojas")
    assert result.intent == IntentType.ANALYSIS


def test_clarification_trigger_for_vague_negative_sales_query():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "quais grupos estão com vendas ruins?",
        "consultar_dados_flexivel",
        0.9,
    )
    assert response is None


def test_no_clarification_when_scope_and_window_are_present():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "top grupos com venda negativa nos últimos 30 dias na UNE 135",
        "consultar_dados_flexivel",
        0.9,
    )
    assert response is None


def test_clarification_when_no_scope_in_query():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "quais estão com venda negativa?",
        "consultar_dados_flexivel",
        0.9,
    )
    assert response is not None
    assert "recorte da análise" in response["result"]["mensagem"].lower()


def test_clarification_when_chart_query_is_missing_metric_and_breakdown():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "gere um gráfico",
        "gerar_grafico_universal_v2",
        0.95,
    )

    assert response is not None
    assert "métrica principal" in response["result"]["mensagem"].lower()
    assert "recorte do gráfico" in response["result"]["mensagem"].lower()


def test_clarification_when_market_query_is_missing_product_subject():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "faça uma pesquisa de mercado",
        "pesquisar_mercado_web",
        0.95,
    )

    assert response is not None
    assert "informe o produto ou sku" in response["result"]["mensagem"].lower()


def test_no_clarification_when_chart_query_has_metric_and_breakdown():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "gere um gráfico de vendas por segmento nos últimos 30 dias",
        "gerar_grafico_universal_v2",
        0.95,
    )

    assert response is None


def test_no_clarification_for_explicit_chart_query_with_broad_scope():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "gere um gráfico de vendas de todos os segmentos em todas as unes",
        "gerar_grafico_universal_v2",
        0.95,
    )

    assert response is None


def test_followup_reference_marker_does_not_match_regular_verb_prefix():
    agent = _agent_stub()

    assert agent._has_followup_reference_marker("gere um gráfico de vendas de todos os segmentos em todas as unes") is False
    assert agent._has_followup_reference_marker("e na Kalunga?") is True


def test_no_clarification_when_dashboard_query_has_business_filters():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE",
        "gerar_grafico_universal_v2",
        0.95,
    )

    assert response is None


def test_deterministic_negative_sales_formats_executive_output():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"NOMEGRUPO": "GRUPO A", "NOMESEGMENTO": "PAPELARIA", "valor": -1000},
            {"NOMEGRUPO": "GRUPO B", "NOMESEGMENTO": "PAPELARIA", "valor": -500},
            {"NOMEGRUPO": "GRUPO C", "NOMESEGMENTO": "PAPELARIA", "valor": 200},
        ]
    }
    response = agent._format_deterministic_result(
        "quais grupos as vendas estão negativa?",
        "consultar_dados_flexivel",
        tool_result,
    )
    msg = response["result"]["mensagem"]
    assert "## Resumo executivo" in msg
    assert "## Tabela operacional" in msg
    assert "## Próximas ações" in msg
    assert "| Ranking | Grupo | Venda (R$) |" in msg
    assert "Evidência:" not in msg
    assert "GRUPO A" in msg


def test_tool_failure_result_detects_success_false_payload():
    agent = _agent_stub()
    assert agent._is_tool_failure_result(
        {"success": False, "mensagem": "Produto 999999 não encontrado"}
    ) is True


def test_format_product_all_stores_result_returns_executive_output():
    agent = _agent_stub()
    response = agent._format_tool_result_for_path(
        "gere um relatório do produto 25 em todas as lojas",
        "analisar_produto_todas_lojas",
        {
            "success": True,
            "produto": 25,
            "nome": "CANETA BIC CRISTAL DURA 1.0 AZUL R.835205",
            "resumo": {
                "total_lojas_com_produto": 35,
                "lojas_com_estoque": 34,
                "lojas_em_ruptura": 5,
                "total_vendas_30d": 1477.0,
                "total_estoque_lojas": 1669.76,
                "estoque_cd": 745.08,
            },
            "top_5_lojas_vendas": [
                {"une": 1685, "nome": "261", "vendas_30d": 161.0, "estoque": 217.0},
                {"une": 1, "nome": "SCR", "vendas_30d": 142.0, "estoque": 152.0},
            ],
            "lojas_em_ruptura": [
                {"une": 2599, "nome": "ITA", "vendas_30d": 58.0, "estoque": 0},
            ],
        },
        {"produto_codigo": 25},
    )

    msg = response["result"]["mensagem"]
    assert "Produto 25" in msg
    assert "encontrado em 35 lojas" in msg
    assert "| Loja (UNE) | Sigla | Venda 30 dias (R$) | Estoque |" in msg
    assert "Rupturas críticas" in msg
    assert "1685" in msg
    assert "2599" in msg


def test_format_product_all_stores_not_found_returns_explicit_message():
    agent = _agent_stub()
    response = agent._format_tool_result_for_path(
        "gere um relatório do produto 999999 em todas as lojas",
        "analisar_produto_todas_lojas",
        {
            "success": False,
            "produto": 999999,
            "mensagem": "Produto 999999 não encontrado na base de dados.",
            "sugestao": "Verifique se o código do produto está correto.",
        },
        {"produto_codigo": 999999},
    )

    msg = response["result"]["mensagem"]
    assert "Produto 999999 não encontrado" in msg
    assert "Sem dados tabulares adicionais" in msg
    assert "Verifique se o código do produto está correto." in msg


def test_should_use_calculation_sandbox_for_sensitivity_queries():
    agent = _agent_stub()
    agent.code_gen_agent = object()

    intent = SimpleNamespace(value="calculation")
    assert agent._should_use_calculation_sandbox(intent, "calcular_eoq", "faça simulação de sensibilidade do eoq")


def test_execute_calculation_sandbox_returns_structured_response():
    class _DummyCodeGen:
        def calculate_eoq_internal(self, demand_annual, order_cost, holding_cost_pct, unit_cost):
            return {
                "eoq": 120,
                "orders_per_year": 10,
                "total_cost": 5400.0,
                "order_point": 60,
            }

    agent = _agent_stub()
    agent.code_gen_agent = _DummyCodeGen()
    agent.bi_tools = []

    tool_selection = SimpleNamespace(tool_params={})
    response = agent._execute_calculation_sandbox(
        "simulação de eoq com demanda anual 12000, custo de pedido 200, custo unitário 10 e 25% de armazenagem",
        tool_selection,
    )

    assert response is not None
    assert response["source"] == "sandbox.code_gen_agent"
    assert response["mode"] == "deterministic_sandbox"
    assert "EOQ recomendado" in response["result"]["mensagem"]


def test_execute_calculation_sandbox_returns_margin_report_from_explicit_numbers():
    class _DummyCodeGen:
        def calculate_eoq_internal(self, demand_annual, order_cost, holding_cost_pct, unit_cost):
            raise AssertionError("EOQ should not be used for margin calculation")

    agent = _agent_stub()
    agent.code_gen_agent = _DummyCodeGen()
    agent.bi_tools = []

    response = agent._execute_calculation_sandbox(
        "calcule a margem do produto com preço de venda 25 e custo unitário 15",
        SimpleNamespace(tool_params={}),
    )

    assert response is not None
    assert response["source"] == "sandbox.code_gen_agent"
    assert "Margem bruta estimada" in response["result"]["mensagem"]
    assert isinstance(response.get("table_data"), list)


def test_execute_calculation_sandbox_returns_stock_coverage_report_from_snapshot():
    class _DummyCodeGen:
        def calculate_eoq_internal(self, demand_annual, order_cost, holding_cost_pct, unit_cost):
            raise AssertionError("EOQ should not be used for stock coverage calculation")

    agent = _agent_stub()
    agent.code_gen_agent = _DummyCodeGen()
    agent.bi_tools = []
    agent._resolve_product_snapshot_for_calculation = lambda query, params: {
        "produto_id": "369947",
        "produto_nome": "TNT 40GRS",
        "venda_30dd": 300.0,
        "estoque_une": 150.0,
        "une_id": 520,
    }

    response = agent._execute_calculation_sandbox(
        "calcule a cobertura em dias do produto 369947 na une 520",
        SimpleNamespace(tool_params={"produto_id": "369947", "une": 520}),
    )

    assert response is not None
    assert "Cobertura estimada" in response["result"]["mensagem"]
    assert any(row["Indicador"] == "Cobertura (dias)" for row in response["table_data"])


@pytest.mark.asyncio
async def test_semantic_tool_fallback_executes_next_valid_tool():
    class _DummyTool:
        def __init__(self, name, result):
            self.name = name
            self._result = result

        def invoke(self, args):
            return self._result

    agent = _agent_stub()
    agent.code_gen_agent = None
    agent.bi_tools = [
        _DummyTool(
            "consultar_dados_flexivel",
            {"status": "success", "resultados": [{"UNE": 520, "VENDA_30DD": 1000}]},
        )
    ]

    recovered = await agent._execute_semantic_tool_fallback(
        user_query="dashboard do segmento artes",
        primary_tool_name="gerar_dashboard_executivo",
        primary_tool_params={"segmento": "ARTES"},
        fallback_tools=["consultar_dados_flexivel"],
        on_progress=None,
    )

    assert recovered is not None
    assert recovered["tool_name"] == "consultar_dados_flexivel"
    assert recovered["tool_result"]["status"] == "success"


@pytest.mark.asyncio
async def test_semantic_tool_fallback_skips_empty_result_and_uses_next_candidate():
    class _DummyTool:
        def __init__(self, name, result):
            self.name = name
            self._result = result

        def invoke(self, args):
            return self._result

    agent = _agent_stub()
    agent.code_gen_agent = None
    agent.bi_tools = [
        _DummyTool("gerar_grafico_universal_v2", {"status": "success", "chart_data": {"data": [], "layout": {}}}),
        _DummyTool(
            "consultar_dados_flexivel",
            {"status": "success", "resultados": [{"UNE": 520, "VENDA_30DD": 1000}]},
        ),
    ]

    recovered = await agent._execute_semantic_tool_fallback(
        user_query="gere um dashboard de vendas por segmento",
        primary_tool_name="gerar_dashboard_executivo",
        primary_tool_params={"segmento": "ARTES"},
        fallback_tools=["gerar_grafico_universal_v2", "consultar_dados_flexivel"],
        on_progress=None,
    )

    assert recovered is not None
    assert recovered["tool_name"] == "consultar_dados_flexivel"


def test_effectively_empty_tool_result_accepts_chart_json_string_payload():
    agent = _agent_stub()

    tool_result = {
        "status": "success",
        "chart_data": '{"data":[{"x":["A"],"y":[10],"type":"bar"}],"layout":{"title":"Teste"}}',
    }

    assert agent._is_effectively_empty_tool_result("gerar_grafico_universal_v2", tool_result) is False


def test_resolve_query_context_keeps_explicit_eoq_query_standalone():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "gere um gráfico de vendas por segmento"},
        {"role": "assistant", "content": "ok"},
    ]

    query = "calcule o EOQ com demanda anual 12000, custo por pedido 150, holding 20% e custo unitário 18"
    resolved = agent._resolve_query_with_history_context(query, chat_history)

    assert resolved == query


def test_resolve_query_context_merges_sensitivity_followup_without_parameters():
    agent = _agent_stub()
    base = "calcule o EOQ com demanda anual 12000, custo por pedido 150, holding 20% e custo unitário 18"
    followup = "faça análise de sensibilidade do EOQ variando demanda em -20%, base e +20%"
    chat_history = [
        {"role": "user", "content": base},
        {"role": "assistant", "content": "ok"},
    ]

    resolved = agent._resolve_query_with_history_context(followup, chat_history)

    assert base in resolved
    assert followup in resolved


def test_resolve_query_context_keeps_commercial_plan_followup_standalone():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "relatório de vendas do produto 369947 em todas as lojas"},
        {"role": "assistant", "content": "ok"},
    ]

    query = "me de um plano comercial para 7 dias"
    resolved = agent._resolve_query_with_history_context(query, chat_history)

    assert resolved == query


def test_resolve_query_context_keeps_contextual_action_followup_standalone():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "gere um gráfico de vendas de todos os segmentos em todas as unes"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 100 |",
            "metadata": {"context": {"response_breakdown": "SEGMENTO", "scope_all_stores": True}},
        },
    ]

    query = "com base na última resposta, quais ações você recomenda?"
    resolved = agent._resolve_query_with_history_context(query, chat_history)

    assert resolved == query


def test_resolve_query_context_expands_short_store_followup_with_previous_product():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "quais 5 lojas mais vendem o produto 59294"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Loja (UNE) | Venda (R$) |\n|---|---|\n| 3 | 4915 |",
            "metadata": {
                "context": {
                    "product_code": 59294,
                    "response_breakdown": "LOJA",
                    "scope_all_stores": True,
                }
            },
        },
    ]

    resolved = agent._resolve_query_with_history_context("e qual vende menos?", chat_history)

    assert resolved == "qual loja vende menos o produto 59294"


def test_resolve_query_context_expands_short_rupture_followup_with_previous_product():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "quais 5 lojas mais vendem o produto 59294"},
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "context": {
                    "product_code": 59294,
                    "response_breakdown": "LOJA",
                    "scope_all_stores": True,
                }
            },
        },
    ]

    resolved = agent._resolve_query_with_history_context("e quais estão em ruptura?", chat_history)

    assert resolved == "quais lojas estão com rupturas do produto 59294"


def test_clarification_for_unanchored_contextual_followup_without_context():
    agent = _agent_stub()
    response = agent._build_clarification_if_needed(
        "e qual vende menos?",
        "consultar_dados_flexivel",
        0.9,
        chat_history=None,
    )

    assert response is not None
    assert "confirme o contexto principal" in response["result"]["mensagem"].lower()


def test_chart_query_enrichment_infers_segment_breakdown():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.4)

    agent._enrich_tool_selection_for_business(
        "gere um gráfico de vendas por segmento nos últimos 90 dias",
        tool_selection,
    )

    assert tool_selection.tool_name == "gerar_grafico_universal_v2"
    assert tool_selection.tool_params.get("quebra_por") == "SEGMENTO"


def test_dashboard_query_enrichment_routes_to_chart_with_une_breakdown_filters():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="gerar_dashboard_executivo", tool_params={}, confidence=0.4)

    agent._enrich_tool_selection_for_business(
        "gere um dashboard interativo do segmento ARTES nos últimos 30 dias com KPIs, tendência e tabela por UNE",
        tool_selection,
    )

    assert tool_selection.tool_name == "gerar_grafico_universal_v2"
    assert tool_selection.tool_params.get("filtro_segmento") == "ARTES"
    assert tool_selection.tool_params.get("quebra_por") == "LOJA"
    assert tool_selection.tool_params.get("periodo") == "30d"


def test_format_tool_result_for_path_promotes_dashboard_contract_when_query_requests_dashboard():
    agent = _agent_stub()
    tool_result = {
        "status": "success",
        "chart_data": {"data": [{"x": ["A"], "y": [10], "type": "bar"}], "layout": {"title": "Teste"}},
        "summary": {"vendas_totais": 10},
    }
    response = agent._format_tool_result_for_path(
        "gere um dashboard interativo de vendas",
        "gerar_grafico_universal_v2",
        tool_result,
        {"segmento": "ARTES"},
    )

    assert response["type"] == "dashboard"
    assert isinstance(response.get("dashboard_spec"), dict)


def test_format_tool_result_for_path_keeps_chart_contract_for_dashboard_followup():
    agent = _agent_stub()
    tool_result = {
        "status": "success",
        "chart_data": {"data": [{"x": ["A"], "y": [10], "type": "bar"}], "layout": {"title": "Teste"}},
        "summary": {
            "dimensao": "Segmento",
            "metrica": "Vendas (R$)",
            "mensagem": "Análise concluída: 2 itens.",
            "bottom_3": [{"dimensao": "DIVERSOS", "valor": 10.0}],
        },
    }
    response = agent._format_tool_result_for_path(
        "com base nesse dashboard, o que você recomenda?",
        "gerar_grafico_universal_v2",
        tool_result,
        {"filtro_segmento": "ARTES", "quebra_por": "SEGMENTO"},
    )

    assert response["type"] == "text"
    assert response.get("chart_data") is not None
    assert response.get("dashboard_spec") is None


def test_format_governed_chart_result_uses_dimension_from_summary_not_hardcoded_une():
    agent = _agent_stub()
    tool_result = {
        "status": "success",
        "summary": {
            "dimensao": "Segmento",
            "metrica": "Vendas (R$)",
            "mensagem": "Análise concluída: 3 itens.",
            "top_3": [
                {"dimensao": "ARMARINHO E CONFECÇÃO", "valor": 881936.53},
                {"dimensao": "PAPELARIA", "valor": 778095.55},
                {"dimensao": "TECIDOS", "valor": 610686.27},
            ],
        },
    }

    response = agent._format_governed_chart_result(
        "gere um gráfico de vendas por segmento nos últimos 90 dias",
        tool_result,
        {"filtro_segmento": "ARTES", "quebra_por": "SEGMENTO"},
    )

    msg = response["result"]["mensagem"]
    assert "| Segmento | Vendas (R$) |" in msg
    assert "| UNE | Vendas (R$) |" not in msg


def test_format_governed_chart_result_uses_bottom_ranking_for_critical_followup():
    agent = _agent_stub()
    tool_result = {
        "status": "success",
        "summary": {
            "dimensao": "Segmento",
            "metrica": "Vendas (R$)",
            "mensagem": "Análise concluída: 6 itens.",
            "top_3": [
                {"dimensao": "PAPELARIA", "valor": 900000.0},
                {"dimensao": "ARTES", "valor": 800000.0},
                {"dimensao": "TECIDOS", "valor": 700000.0},
            ],
            "bottom_3": [
                {"dimensao": "DIVERSOS", "valor": 15000.0},
                {"dimensao": "USO CONSUMO", "valor": 12000.0},
                {"dimensao": "SERVICOS", "valor": 9000.0},
            ],
        },
    }

    response = agent._format_governed_chart_result(
        "com base nesse dashboard, detalhe os pontos críticos",
        tool_result,
        {"quebra_por": "SEGMENTO"},
    )

    msg = response["result"]["mensagem"]
    assert "DIVERSOS" in msg
    assert "USO CONSUMO" in msg
    assert "SERVICOS" in msg
    assert "PAPELARIA" not in msg


def test_dashboard_from_chart_includes_top_table_and_filters():
    agent = _agent_stub()
    top_entries = [
        {"dimensao": str(1000 + idx), "valor": float(100000 - idx * 1000)}
        for idx in range(10)
    ]
    tool_result = {
        "status": "success",
        "chart_data": {"data": [{"x": ["1685", "2365"], "y": [311492.84, 271045.33], "type": "bar"}]},
        "summary": {
            "dimensao": "Loja (UNE)",
            "metrica": "Vendas (R$)",
            "top_10": top_entries,
        },
    }

    response = agent._format_tool_result_for_path(
        "gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE",
        "gerar_grafico_universal_v2",
        tool_result,
        {"filtro_segmento": "ARTES", "periodo": "30d"},
    )

    assert response["type"] == "dashboard"
    dashboard_spec = response.get("dashboard_spec", {})
    assert dashboard_spec.get("filters", {}).get("segmento") == "ARTES"
    assert dashboard_spec.get("filters", {}).get("periodo") == "Últimos 30 dias"
    table_widgets = [w for w in dashboard_spec.get("widgets", []) if w.get("kind") == "table"]
    assert table_widgets
    ranking_tables = [w for w in table_widgets if "Top 10" in str(w.get("title"))]
    assert ranking_tables
    assert len(ranking_tables[0].get("rows", [])) == 10
    assert "segmento=ARTES" not in str(dashboard_spec.get("subtitle", ""))


def test_market_research_discards_irrelevant_hits_for_nonexistent_item():
    agent = _agent_stub()
    tool_result = {
        "itens": [
            {"concorrente": "Mercado Livre", "produto": "Livro O cavaleiro inexistente", "preco": 61.0},
            {"concorrente": "Mercado Livre", "produto": "Tarô Waite Edição Especial", "preco": 52.0},
        ],
        "fontes_consultadas": [],
        "escopo": {"estado": "RJ"},
    }

    response = agent._format_deterministic_result(
        "pesquisa de mercado de produto inexistente xyz-abc-999 no RJ",
        "pesquisar_precos_concorrentes",
        tool_result,
    )

    msg = response["result"]["mensagem"].lower()
    assert "sem preço público confiável" in msg
    assert "baixa aderência ao item solicitado" in msg


def test_market_research_keeps_relevant_hits_when_query_matches_product():
    agent = _agent_stub()
    tool_result = {
        "itens": [
            {
                "concorrente": "Kalunga",
                "produto": "Caderno Universitário Capa Dura 10 matérias 160 folhas",
                "preco": 39.90,
                "url": "https://www.kalunga.com.br/produto/caderno-universitario",
            },
            {
                "concorrente": "Amazon",
                "produto": "Caderno universitário espiral 80 folhas",
                "preco": 29.99,
                "url": "https://www.amazon.com.br/caderno-universitario",
            },
        ],
        "fontes_consultadas": [],
        "escopo": {"estado": "RJ"},
    }

    response = agent._format_deterministic_result(
        "faça uma pesquisa de mercado de caderno universitário em RJ com fontes públicas e links",
        "pesquisar_precos_concorrentes",
        tool_result,
    )

    msg = response["result"]["mensagem"]
    assert "Pesquisa concorrencial concluída com 2 referências" in msg
    assert "Caderno Universitário" in msg


def test_analisar_produto_todas_lojas_answers_store_leader_question_directly():
    agent = _agent_stub()
    tool_result = {
        "success": True,
        "produto": 369947,
        "nome": "LAPIS TESTE",
        "resumo": {
            "total_lojas_com_produto": 3,
            "lojas_com_estoque": 3,
            "lojas_em_ruptura": 0,
            "total_vendas_30d": 4200.0,
            "total_estoque_lojas": 180.0,
            "estoque_cd": 200.0,
        },
        "top_5_lojas_vendas": [
            {"une": 1685, "nome": "SCR", "vendas_30d": 1800.0, "estoque": 42.0},
            {"une": 520, "nome": "RBR", "vendas_30d": 1300.0, "estoque": 55.0},
            {"une": 35, "nome": "NIT", "vendas_30d": 1100.0, "estoque": 83.0},
        ],
        "lojas_em_ruptura": [],
    }

    response = agent._format_deterministic_result(
        "qual loja mais vende o produto 369947 ?",
        "analisar_produto_todas_lojas",
        tool_result,
        {"produto_codigo": 369947},
    )

    msg = response["result"]["mensagem"]
    assert "A loja que mais vende o produto 369947" in msg
    assert "UNE 1685" in msg
    assert "| Loja (UNE) | Sigla | Venda 30 dias (R$) | Estoque |" in msg


def test_consultar_dados_flexivel_formats_top_five_store_ranking_for_product():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"UNE": 3, "valor": 4915.0},
            {"UNE": 1, "valor": 3667.0},
            {"UNE": 57, "valor": 2999.0},
            {"UNE": 2586, "valor": 2991.0},
            {"UNE": 79, "valor": 2348.0},
            {"UNE": 135, "valor": 1800.0},
        ]
    }

    response = agent._format_deterministic_result(
        "quais 5 lojas mais vendem o produto 59294",
        "consultar_dados_flexivel",
        tool_result,
        {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["UNE"],
            "ordenar_por": "valor",
            "ordem_desc": True,
            "limite": 5,
            "filtros": {"PRODUTO": 59294},
        },
    )

    msg = response["result"]["mensagem"]
    assert "Top 5 lojas por venda do produto 59294" in msg
    assert "| Loja (UNE) | Venda (R$) |" in msg
    assert "| 3 |" in msg
    assert "| 135 |" not in msg


def test_consultar_dados_flexivel_formats_lowest_store_for_product():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"UNE": 2401, "valor": 200.0},
            {"UNE": 3281, "valor": 202.2},
            {"UNE": 3577, "valor": 308.92},
        ]
    }

    response = agent._format_deterministic_result(
        "qual loja vende menos o produto 369947",
        "consultar_dados_flexivel",
        tool_result,
        {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": ["UNE"],
            "ordenar_por": "valor",
            "ordem_desc": False,
            "limite": 1,
            "filtros": {"PRODUTO": 369947},
        },
    )

    msg = response["result"]["mensagem"]
    assert "A loja que menos vende o produto 369947 é a UNE 2401" in msg
    assert "| Loja (UNE) | Venda (R$) |" in msg


def test_analisar_produto_todas_lojas_formats_rupture_store_list_for_product():
    agent = _agent_stub()
    tool_result = {
        "success": True,
        "produto": 369947,
        "nome": "TNT 40GRS",
        "resumo": {
            "total_lojas_com_produto": 36,
            "lojas_com_estoque": 30,
            "lojas_em_ruptura": 2,
            "total_vendas_30d": 12000.0,
            "total_estoque_lojas": 5400.0,
            "estoque_cd": 320.0,
        },
        "top_5_lojas_vendas": [],
        "lojas_em_ruptura": [
            {"une": 2365, "nome": "RBR", "vendas_30d": 45.0, "estoque": 0.0},
            {"une": 2586, "nome": "NIG", "vendas_30d": 12.0, "estoque": 0.0},
        ],
    }

    response = agent._format_deterministic_result(
        "quais lojas estão com rupturas do produto 369947",
        "analisar_produto_todas_lojas",
        tool_result,
        {"produto_codigo": 369947},
    )

    msg = response["result"]["mensagem"]
    assert "Identifiquei 2 loja(s) em ruptura do produto 369947" in msg
    assert "| Loja (UNE) | Sigla | Venda 30 dias (R$) | Estoque |" in msg
    assert "2365" in msg


def test_calcular_mc_produto_formats_operational_report():
    agent = _agent_stub()
    response = agent._format_deterministic_result(
        "qual a média comum do produto 369947 na une 520",
        "calcular_mc_produto",
        {
            "produto_id": 369947,
            "une_id": 520,
            "nome": "TNT 40GRS",
            "segmento": "TECIDOS",
            "mc_calculada": 42.5,
            "estoque_atual": 30.0,
            "linha_verde": 60.0,
            "percentual_linha_verde": 50.0,
            "recomendacao": "Planejar abastecimento",
        },
        {"produto_id": 369947, "une_id": 520},
    )

    msg = response["result"]["mensagem"]
    assert "MC calculada para o produto 369947" in msg
    assert "TNT 40GRS" in msg
    assert "| Indicador | Valor |" in msg


def test_calcular_preco_final_une_formats_policy_report():
    agent = _agent_stub()
    response = agent._format_deterministic_result(
        "calcule o preço final para compra de 1000 no ranking 2 à vista",
        "calcular_preco_final_une",
        {
            "valor_original": 1000.0,
            "tipo": "Atacado",
            "ranking": 2,
            "desconto_ranking": "38%",
            "forma_pagamento": "vista",
            "desconto_pagamento": "38%",
            "preco_final": 384.4,
            "economia": 615.6,
        },
        {"valor_compra": 1000.0, "ranking": 2, "forma_pagamento": "vista"},
    )

    msg = response["result"]["mensagem"]
    assert "Cálculo de preço final concluído" in msg
    assert "Ranking" not in msg or "ranking" in msg.lower()
    assert "| Indicador | Valor |" in msg


def test_consultar_dados_flexivel_aggregated_segment_returns_executive_table():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"NOMESEGMENTO": "ARTES", "valor": 319947.0},
            {"NOMESEGMENTO": "PAPELARIA", "valor": 778096.0},
            {"NOMESEGMENTO": "TECIDOS", "valor": 610686.0},
        ]
    }

    response = agent._format_deterministic_result(
        "gere um gráfico de vendas por segmento nos últimos 90 dias",
        "consultar_dados_flexivel",
        tool_result,
    )

    msg = response["result"]["mensagem"]
    assert "Consolidado de vendas por segmento concluído" in msg
    assert "| Segmento | Venda (R$) |" in msg
    assert "Código do produto" not in msg
    assert isinstance(response.get("table_data"), list)
    assert len(response["table_data"]) == 3
    assert response["table_data"][0]["NOMESEGMENTO"] == "PAPELARIA"


def test_consultar_dados_flexivel_aggregated_segment_returns_enriched_sales_report():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"NOMESEGMENTO": "ARTES", "valor": 319947.0},
            {"NOMESEGMENTO": "PAPELARIA", "valor": 778096.0},
            {"NOMESEGMENTO": "TECIDOS", "valor": 610686.0},
            {"NOMESEGMENTO": "AVIAMENTOS", "valor": 152340.0},
            {"NOMESEGMENTO": "DECORACAO", "valor": 104210.0},
            {"NOMESEGMENTO": "FESTAS", "valor": 82110.0},
        ]
    }

    response = agent._format_deterministic_result(
        "preciso de um relatório de vendas do segmento tecidos de todas as lojas",
        "consultar_dados_flexivel",
        tool_result,
        {"filtros": {"NOMESEGMENTO": "TECIDOS", "periodo": "90d"}},
    )

    msg = response["result"]["mensagem"]
    assert "## Resumo executivo" in msg
    assert "KPIs-chave" in msg
    assert "Filtros aplicados" in msg
    assert "| Segmento | Venda (R$) | Part. % | Ranking | Gap p/ média (R$) | Classificação |" in msg
    assert "PAPELARIA" in msg
    assert "TECIDOS" in msg
    assert "Próximas ações" in msg
    assert isinstance(response.get("table_data"), list)
    assert response["table_data"][0]["NOMESEGMENTO"] == "PAPELARIA"
    assert "TOTAL_VENDAS" in response["table_data"][0]


def test_consultar_dados_flexivel_sales_plan_followup_generates_7_day_action_plan():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"UNE": 2586, "valor": 2500.0},
            {"UNE": 1, "valor": 2100.0},
            {"UNE": 520, "valor": 1834.26},
            {"UNE": 35, "valor": 1008.98},
        ]
    }

    response = agent._format_deterministic_result(
        "relatório de vendas do produto 369947 em todas as lojas. me de um plano comercial para 7 dias",
        "consultar_dados_flexivel",
        tool_result,
    )

    msg = response["result"]["mensagem"]
    assert "Plano comercial de 7 dias" in msg
    assert "Gap para média (R$)" in msg
    assert "Dia 1" in msg
    assert "Dia 7" in msg
    assert isinstance(response.get("table_data"), list)
    assert str(response["table_data"][0]["UNE"]) == "35"


def test_consultar_dados_flexivel_aggregated_une_returns_enriched_sales_report():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"UNE": 1685, "valor": 311492.84},
            {"UNE": 2365, "valor": 271045.33},
            {"UNE": 1, "valor": 206161.63},
            {"UNE": 520, "valor": 154720.52},
            {"UNE": 81, "valor": 125054.02},
        ]
    }

    response = agent._format_deterministic_result(
        "preciso de um relatório de vendas do segmento tecidos de todas as lojas",
        "consultar_dados_flexivel",
        tool_result,
        {"filtros": {"NOMESEGMENTO": "TECIDOS"}},
    )

    msg = response["result"]["mensagem"]
    assert "consolidado de vendas por loja (une) concluído" in msg.lower()
    assert "KPIs-chave" in msg
    assert "| Loja (UNE) | Venda (R$) | Part. % | Ranking | Gap p/ média (R$) | Classificação |" in msg
    assert "1685" in msg
    assert "2365" in msg
    assert isinstance(response.get("table_data"), list)
    assert str(response["table_data"][0]["UNE"]) == "1685"
    assert "TOTAL_VENDAS" in response["table_data"][0]


def test_commercial_plan_followup_routes_to_aggregated_une_query_from_history():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.4)
    chat_history = [
        {"role": "user", "content": "gere um gráfico de vendas de todos os segmentos em todas as unes"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 100 |",
            "metadata": {"context": {"response_breakdown": "SEGMENTO", "scope_all_stores": True}},
        },
    ]

    agent._enrich_tool_selection_for_business(
        "me de um plano comercial de 7 dias para as unes de menor venda",
        tool_selection,
        chat_history=chat_history,
    )

    assert tool_selection.tool_name == "consultar_dados_flexivel"
    assert tool_selection.tool_params.get("agrupar_por") == ["UNE"]
    assert tool_selection.tool_params.get("ordem_desc") is False
    assert tool_selection.tool_params.get("limite") == 200


def test_commercial_plan_followup_infers_product_filter_from_previous_user_query():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.4)
    chat_history = [
        {"role": "user", "content": "relatório de vendas do produto 369947 em todas as lojas"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Loja (UNE) | Venda (R$) |\n|---|---|\n| 2586 | 2500 |",
            "metadata": {"context": {"response_breakdown": "LOJA", "scope_all_stores": True}},
        },
    ]

    agent._enrich_tool_selection_for_business(
        "me de um plano comercial para 7 dias",
        tool_selection,
        chat_history=chat_history,
    )

    assert tool_selection.tool_name == "consultar_dados_flexivel"
    assert tool_selection.tool_params.get("agrupar_por") == ["UNE"]
    assert tool_selection.tool_params.get("filtros", {}).get("PRODUTO") == 369947


def test_commercial_plan_with_raw_rows_never_falls_back_to_generic_table_dump():
    agent = _agent_stub()
    tool_result = {
        "resultados": [
            {"UNE": 2586, "PRODUTO": 704559, "VENDA_30DD": 0, "ESTOQUE_UNE": 0},
            {"UNE": 2586, "PRODUTO": 704563, "VENDA_30DD": 0, "ESTOQUE_UNE": 1},
            {"UNE": 520, "PRODUTO": 704581, "VENDA_30DD": 120, "ESTOQUE_UNE": 6},
            {"UNE": 35, "PRODUTO": 704583, "VENDA_30DD": 80, "ESTOQUE_UNE": 1.53},
        ]
    }

    response = agent._format_deterministic_result(
        "me de um plano comercial de 7 dias para as unes de menor venda",
        "consultar_dados_flexivel",
        tool_result,
    )

    msg = response["result"]["mensagem"]
    assert "Plano comercial de 7 dias" in msg
    assert "Gap para média (R$)" in msg
    assert "Consulta executada com sucesso" not in msg


def test_reference_examples_are_disabled_for_contextual_followup_with_session_context():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.92)
    chat_history = [
        {"role": "user", "content": "gere um gráfico de vendas por segmento"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 100 |",
            "metadata": {"context": {"response_breakdown": "SEGMENTO"}},
        },
    ]

    should_use = agent._should_use_reference_examples(
        "com base na última resposta, detalhe as próximas ações",
        tool_selection=tool_selection,
        chat_history=chat_history,
    )

    assert should_use is False


def test_contextual_action_followup_routes_to_commercial_plan_from_history():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.4)
    chat_history = [
        {"role": "user", "content": "gere um gráfico de vendas de todos os segmentos em todas as unes"},
        {
            "role": "assistant",
            "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 100 |",
            "metadata": {"context": {"response_breakdown": "SEGMENTO", "scope_all_stores": True}},
        },
    ]

    agent._enrich_tool_selection_for_business(
        "com base na última resposta, quais ações você recomenda?",
        tool_selection,
        chat_history=chat_history,
    )

    assert tool_selection.tool_name == "consultar_dados_flexivel"
    assert tool_selection.tool_params.get("agrupar_por") == ["NOMESEGMENTO"]
    assert tool_selection.tool_params.get("ordem_desc") is False


def test_dashboard_followup_routes_to_chart_with_previous_filters():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="gerar_dashboard_executivo", tool_params={}, confidence=0.4)
    chat_history = [
        {
            "role": "user",
            "content": "gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE",
        },
        {
            "role": "assistant",
            "content": "Dashboard interativo gerado com sucesso.",
            "metadata": {
                "context": {
                    "response_type": "dashboard",
                    "has_dashboard": True,
                    "response_breakdown": "LOJA",
                    "segment": "ARTES",
                    "period": "30d",
                    "dashboard_filters": {"segmento": "ARTES", "periodo": "30d"},
                }
            },
        },
    ]

    agent._enrich_tool_selection_for_business(
        "com base nesse dashboard, detalhe os pontos críticos",
        tool_selection,
        chat_history=chat_history,
    )

    assert tool_selection.tool_name == "gerar_grafico_universal_v2"
    assert tool_selection.tool_params.get("quebra_por") == "LOJA"
    assert tool_selection.tool_params.get("filtro_segmento") == "ARTES"
    assert "menores vendas" in tool_selection.tool_params.get("descricao", "")


def test_market_followup_routes_specific_competitor_using_previous_product_context():
    agent = _agent_stub()
    tool_selection = SimpleNamespace(tool_name="consultar_dados_flexivel", tool_params={}, confidence=0.4)
    chat_history = [
        {
            "role": "user",
            "content": "faça uma pesquisa de mercado do produto lapis de cor 12 cores",
            "metadata": {"context": {"market_product_hint": "lapis de cor 12 cores"}},
        },
        {
            "role": "assistant",
            "content": "## Resumo executivo\n- Pesquisa de mercado concluida para **lapis de cor 12 cores** com 15 referencias.",
            "metadata": {
                "context": {
                    "source": "tool.pesquisar_mercado_web",
                    "market_product_hint": "lapis de cor 12 cores",
                }
            },
        },
    ]

    agent._enrich_tool_selection_for_business(
        "e na Kalunga?",
        tool_selection,
        chat_history=chat_history,
    )

    assert tool_selection.tool_name == "pesquisar_precos_concorrentes"
    assert "lapis de cor 12 cores" in tool_selection.tool_params.get("descricao_produto", "").lower()
    assert tool_selection.tool_params.get("concorrentes") == "kalunga"


def test_should_attempt_routed_tool_rescue_for_high_confidence_chart_query():
    class _DummyTool:
        name = "gerar_grafico_universal_v2"

        def invoke(self, args):
            return {"status": "success"}

    agent = _agent_stub()
    agent.bi_tools = [_DummyTool()]
    tool_selection = SimpleNamespace(tool_name="gerar_grafico_universal_v2", tool_params={}, confidence=0.9)

    should_rescue = agent._should_attempt_routed_tool_rescue(
        "gere um gráfico de vendas por segmento",
        "Posso te ajudar com essa análise.",
        tool_selection,
        successful_tool_calls=0,
    )

    assert should_rescue is True


@pytest.mark.asyncio
async def test_attempt_routed_tool_rescue_executes_selected_tool_and_formats_response():
    class _DummyTool:
        name = "gerar_grafico_universal_v2"

        def invoke(self, args):
            return {
                "status": "success",
                "chart_data": {"data": [], "layout": {"title": "Teste"}},
                "summary": {
                    "dimensao": "Segmento",
                    "metrica": "Vendas (R$)",
                    "mensagem": "Análise concluída: 1 item.",
                    "top_3": [{"dimensao": "PAPELARIA", "valor": 100.0}],
                },
            }

    agent = _agent_stub()
    agent.bi_tools = [_DummyTool()]
    agent.code_gen_agent = None

    tool_selection = SimpleNamespace(
        tool_name="gerar_grafico_universal_v2",
        tool_params={"descricao": "gere um gráfico de vendas por segmento", "quebra_por": "SEGMENTO"},
        confidence=0.9,
        fallback_tools=[],
    )

    response = await agent._attempt_routed_tool_rescue(
        "gere um gráfico de vendas por segmento",
        tool_selection,
        on_progress=None,
    )

    assert response is not None
    assert response.get("chart_data") is not None
    assert "| Segmento | Vendas (R$) |" in response["result"]["mensagem"]


def test_attempt_routed_tool_rescue_sync_executes_selected_tool_and_formats_response():
    class _DummyTool:
        name = "gerar_grafico_universal_v2"

        def invoke(self, args):
            return {
                "status": "success",
                "chart_data": {"data": [], "layout": {"title": "Teste Sync"}},
                "summary": {
                    "dimensao": "Segmento",
                    "metrica": "Vendas (R$)",
                    "mensagem": "Análise concluída: 1 item.",
                    "top_3": [{"dimensao": "PAPELARIA", "valor": 100.0}],
                },
            }

    agent = _agent_stub()
    agent.bi_tools = [_DummyTool()]
    agent.code_gen_agent = None

    tool_selection = SimpleNamespace(
        tool_name="gerar_grafico_universal_v2",
        tool_params={"descricao": "gere um gráfico de vendas por segmento", "quebra_por": "SEGMENTO"},
        confidence=0.9,
        fallback_tools=[],
    )

    response = agent._attempt_routed_tool_rescue_sync(
        "gere um gráfico de vendas por segmento",
        tool_selection,
    )

    assert response is not None
    assert response.get("chart_data") is not None
    assert "| Segmento | Vendas (R$) |" in response["result"]["mensagem"]


def test_semantic_tool_fallback_sync_executes_next_valid_tool():
    class _DummyTool:
        def __init__(self, name, result):
            self.name = name
            self._result = result

        def invoke(self, args):
            return self._result

    agent = _agent_stub()
    agent.code_gen_agent = None
    agent.bi_tools = [
        _DummyTool(
            "consultar_dados_flexivel",
            {"status": "success", "resultados": [{"UNE": 520, "VENDA_30DD": 1000}]},
        )
    ]

    recovered = agent._execute_semantic_tool_fallback_sync(
        user_query="dashboard do segmento artes",
        primary_tool_name="gerar_dashboard_executivo",
        primary_tool_params={"segmento": "ARTES"},
        fallback_tools=["consultar_dados_flexivel"],
    )

    assert recovered is not None
    assert recovered["tool_name"] == "consultar_dados_flexivel"
    assert recovered["tool_result"]["status"] == "success"


@pytest.mark.asyncio
async def test_attempt_routed_tool_rescue_recovers_after_primary_exception():
    class _BrokenTool:
        name = "gerar_dashboard_executivo"

        def invoke(self, args):
            raise RuntimeError("dashboard indisponível")

    class _FallbackTool:
        name = "consultar_dados_flexivel"

        def invoke(self, args):
            return {
                "status": "success",
                "resultados": [
                    {"NOMESEGMENTO": "ARTES", "valor": 1200.0},
                    {"NOMESEGMENTO": "PAPELARIA", "valor": 950.0},
                ],
            }

    agent = _agent_stub()
    agent.code_gen_agent = None
    agent.bi_tools = [_BrokenTool(), _FallbackTool()]

    tool_selection = SimpleNamespace(
        tool_name="gerar_dashboard_executivo",
        tool_params={"segmento": "ARTES"},
        confidence=0.9,
        fallback_tools=["consultar_dados_flexivel"],
    )

    response = await agent._attempt_routed_tool_rescue(
        "gere um dashboard de vendas por segmento",
        tool_selection,
        on_progress=None,
    )

    assert response is not None
    assert "Tabela operacional" in response["result"]["mensagem"]
    assert "ARTES" in response["result"]["mensagem"]


def test_attempt_routed_tool_rescue_sync_recovers_after_primary_exception():
    class _BrokenTool:
        name = "gerar_dashboard_executivo"

        def invoke(self, args):
            raise RuntimeError("dashboard indisponível")

    class _FallbackTool:
        name = "consultar_dados_flexivel"

        def invoke(self, args):
            return {
                "status": "success",
                "resultados": [
                    {"NOMESEGMENTO": "ARTES", "valor": 1200.0},
                    {"NOMESEGMENTO": "PAPELARIA", "valor": 950.0},
                ],
            }

    agent = _agent_stub()
    agent.code_gen_agent = None
    agent.bi_tools = [_BrokenTool(), _FallbackTool()]

    tool_selection = SimpleNamespace(
        tool_name="gerar_dashboard_executivo",
        tool_params={"segmento": "ARTES"},
        confidence=0.9,
        fallback_tools=["consultar_dados_flexivel"],
    )

    response = agent._attempt_routed_tool_rescue_sync(
        "gere um dashboard de vendas por segmento",
        tool_selection,
    )

    assert response is not None
    assert "Tabela operacional" in response["result"]["mensagem"]
    assert "ARTES" in response["result"]["mensagem"]


@pytest.mark.asyncio
async def test_run_async_executes_llm_tool_calls_in_parallel(monkeypatch):
    class _ToolCallingLLM:
        def __init__(self):
            self.calls = 0

        def get_completion(self, messages, tools=None, task_type=None):
            self.calls += 1
            if self.calls == 1:
                return {
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "function": {
                                "name": "pesquisar_precos_concorrentes",
                                "arguments": '{"descricao_produto":"lapis de cor 12 cores","limite":"3"}',
                            },
                        },
                        {
                            "id": "call-2",
                            "function": {
                                "name": "pesquisar_mercado_web",
                                "arguments": '{"termo_pesquisa":"lapis de cor 12 cores","limite":"3"}',
                            },
                        },
                    ]
                }
            return {"content": "Pesquisa consolidada concluída."}

    class _SlowTool:
        def __init__(self, name):
            self.name = name

        def invoke(self, args):
            time.sleep(0.25)
            return {
                "status": "success",
                "itens": [{"produto": "lapis de cor 12 cores", "preco": 12.9}],
                "total_itens": 1,
                "mensagem": "Pesquisa concluída.",
            }

    agent = _agent_stub()
    agent.llm = _ToolCallingLLM()
    agent.bi_tools = [
        _SlowTool("pesquisar_precos_concorrentes"),
        _SlowTool("pesquisar_mercado_web"),
    ]
    agent.gemini_tools = []
    agent.enable_rag = False
    agent.retriever = None
    agent.code_gen_agent = None

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(
            intent=SimpleNamespace(value="market_research"),
            confidence=0.6,
            matched_patterns=["market"],
        ),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="pesquisar_precos_concorrentes",
            tool_params={"descricao_produto": "lapis de cor 12 cores", "limite": "3"},
            confidence=0.6,
            fallback_tools=[],
            reasoning="parallel_tool_call_test",
        ),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.field_mapper.FieldMapper.get_essential_columns",
        lambda self: ["PRODUTO", "VENDA_30DD"],
    )
    monkeypatch.setattr(CaculinhaBIAgent, "_requires_governed_path", lambda *args, **kwargs: False)
    monkeypatch.setattr(CaculinhaBIAgent, "_should_use_deterministic_path", lambda *args, **kwargs: False)
    monkeypatch.setattr(CaculinhaBIAgent, "_should_use_reference_examples", lambda *args, **kwargs: False)

    started_at = time.monotonic()
    response = await agent.run_async("faça uma pesquisa de mercado do lapis de cor 12 cores", [])
    elapsed = time.monotonic() - started_at

    assert response is not None
    assert elapsed < 0.45


def test_infer_semantic_fallback_tools_is_query_aware_for_dashboard_requests():
    agent = _agent_stub()

    fallbacks = agent._infer_semantic_fallback_tools(
        primary_tool_name="consultar_dados_flexivel",
        configured_fallbacks=[],
        user_query="gere um dashboard interativo de vendas por segmento",
    )

    assert fallbacks[0] == "gerar_grafico_universal_v2"
    assert "consultar_dados_flexivel" not in fallbacks


def test_infer_semantic_fallback_tools_avoids_chart_for_grounded_product_store_query():
    agent = _agent_stub()

    fallbacks = agent._infer_semantic_fallback_tools(
        primary_tool_name="consultar_dados_flexivel",
        configured_fallbacks=["gerar_grafico_universal_v2"],
        user_query="qual loja vende menos o produto 369947",
    )

    assert "gerar_grafico_universal_v2" not in fallbacks
    assert fallbacks[0] == "analisar_produto_todas_lojas"


def test_infer_semantic_fallback_tools_disables_secondary_fallback_for_product_rupture_query():
    agent = _agent_stub()

    fallbacks = agent._infer_semantic_fallback_tools(
        primary_tool_name="analisar_produto_todas_lojas",
        configured_fallbacks=["consultar_dados_flexivel", "gerar_grafico_universal_v2"],
        user_query="quais lojas estão com rupturas do produto 369947",
    )

    assert "gerar_grafico_universal_v2" not in fallbacks
    assert "consultar_dados_flexivel" not in fallbacks


def test_run_sync_rescues_contextual_plan_query_without_repeating_previous_dump(monkeypatch):
    class _DummyTool:
        name = "consultar_dados_flexivel"

        def invoke(self, args):
            return {
                "status": "success",
                "resultados": [
                    {"UNE": 2586, "valor": 2500.0},
                    {"UNE": 1, "valor": 2100.0},
                    {"UNE": 35, "valor": 1008.98},
                ],
            }

    agent = _agent_stub()
    agent.bi_tools = [_DummyTool()]
    agent.gemini_tools = []
    agent.enable_rag = False
    agent.retriever = None
    agent.code_gen_agent = None
    agent._llm_get_completion = lambda messages, tools, llm_task_type: {
        "content": "Posso te ajudar com um plano comercial."
    }

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(intent=SimpleNamespace(value="analysis"), confidence=0.9),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="consultar_dados_flexivel",
            tool_params={"agrupar_por": ["UNE"]},
            confidence=0.9,
            fallback_tools=[],
        ),
    )
    monkeypatch.setattr(CaculinhaBIAgent, "_requires_governed_path", lambda *args, **kwargs: False)
    monkeypatch.setattr(CaculinhaBIAgent, "_should_use_deterministic_path", lambda *args, **kwargs: False)

    response = agent.run(
        "me de um plano comercial de 7 dias para as unes de menor venda",
        chat_history=[
            {"role": "user", "content": "gere um gráfico de vendas de todos os segmentos em todas as unes"},
            {
                "role": "assistant",
                "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 100 |",
                "metadata": {"context": {"response_breakdown": "SEGMENTO", "scope_all_stores": True}},
            },
        ],
    )

    msg = response["result"]["mensagem"]
    assert "Plano comercial de 7 dias" in msg
    assert "Gap para média (R$)" in msg
    assert "Código do produto" not in msg


def test_run_sync_rescues_contextual_action_followup_with_generic_wording(monkeypatch):
    class _DummyTool:
        name = "consultar_dados_flexivel"

        def invoke(self, args):
            return {
                "status": "success",
                "resultados": [
                    {"NOMESEGMENTO": "INFORMATICA", "valor": 48538.22},
                    {"NOMESEGMENTO": "HIGIENE E BELEZA", "valor": 54402.00},
                    {"NOMESEGMENTO": "PAPELARIA", "valor": 778095.55},
                ],
            }

    agent = _agent_stub()
    agent.bi_tools = [_DummyTool()]
    agent.gemini_tools = []
    agent.enable_rag = False
    agent.retriever = None
    agent.code_gen_agent = None
    agent._llm_get_completion = lambda messages, tools, llm_task_type: {
        "content": "Posso sugerir alguns próximos passos."
    }

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(intent=SimpleNamespace(value="analysis"), confidence=0.9),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="consultar_dados_flexivel",
            tool_params={"agrupar_por": ["NOMESEGMENTO"]},
            confidence=0.9,
            fallback_tools=[],
        ),
    )
    monkeypatch.setattr(CaculinhaBIAgent, "_requires_governed_path", lambda *args, **kwargs: False)
    monkeypatch.setattr(CaculinhaBIAgent, "_should_use_deterministic_path", lambda *args, **kwargs: False)

    response = agent.run(
        "com base na última resposta, quais ações você recomenda?",
        chat_history=[
            {"role": "user", "content": "gere um gráfico de vendas de todos os segmentos em todas as unes"},
            {
                "role": "assistant",
                "content": "## Tabela operacional\n| Segmento | Vendas (R$) |\n|---|---|\n| PAPELARIA | 778.095,55 |",
                "metadata": {"context": {"response_breakdown": "SEGMENTO", "scope_all_stores": True}},
            },
        ],
    )

    msg = response["result"]["mensagem"]
    assert "Plano comercial de 7 dias" in msg
    assert "Segmento" in msg


def test_market_research_followup_builds_negotiation_recommendation_from_history():
    agent = _agent_stub()
    chat_history = [
        {"role": "user", "content": "faça uma pesquisa de mercado do produto lapis de cor 12 cores"},
        {
            "role": "assistant",
            "content": (
                "## Resumo executivo\n"
                "- Pesquisa concorrencial concluída com 4 referências.\n"
                "- Faixa de preço encontrada: R$ 12,90 a R$ 18,50.\n"
                "- Preço médio de referência: R$ 15,40.\n"
            ),
            "metadata": {"context": {"source": "pesquisar_mercado_web"}},
        },
    ]

    response = agent._build_contextual_followup_response(
        "com base nessa pesquisa, o que você recomenda para negociação?",
        chat_history,
    )

    assert response is not None
    assert response["source"] == "context.market_research_followup"
    msg = response["result"]["mensagem"]
    assert "Recomendação de negociação" in msg
    assert "lapis de cor 12 cores" in msg.lower()
    assert "R$ 15,40" in msg


def test_semantic_fallback_chart_params_preserve_segment_une_and_breakdown():
    agent = _agent_stub()
    params = agent._build_semantic_fallback_params(
        "gere um dashboard do segmento ARTES por UNE 1685",
        "gerar_grafico_universal_v2",
        {"segmento": "ARTES"},
    )

    assert params.get("filtro_segmento") == "ARTES"
    assert params.get("filtro_une") == "1685"
    assert params.get("quebra_por") == "LOJA"


def test_semantic_fallback_query_params_preserve_aggregation_for_chart_intent():
    agent = _agent_stub()
    params = agent._build_semantic_fallback_params(
        "gere um gráfico de vendas por segmento nos últimos 90 dias",
        "consultar_dados_flexivel",
        {},
    )

    assert params.get("agregacao") == "SUM"
    assert params.get("coluna_agregacao") == "VENDA_30DD"
    assert params.get("agrupar_por") == ["NOMESEGMENTO"]
    assert params.get("ordenar_por") == "valor"


def test_calculation_sandbox_output_contains_sensitivity_table_when_requested():
    agent = _agent_stub()
    response = agent._format_calculation_sandbox_result(
        "faça análise de sensibilidade do EOQ",
        {
            "eoq": 1000,
            "orders_per_year": 12,
            "total_cost": 3600.0,
            "order_point": 500,
        },
        {
            "produto_id": None,
            "produto_nome": None,
            "demand_annual": 12000.0,
            "order_cost": 150.0,
            "unit_cost": 18.0,
            "holding_cost_pct": 0.2,
            "from_database": False,
        },
        sensitivity=[
            {"cenario": "-20%", "demand_annual": 9600, "eoq": 894, "orders_per_year": 10.7},
            {"cenario": "Base", "demand_annual": 12000, "eoq": 1000, "orders_per_year": 12.0},
            {"cenario": "+20%", "demand_annual": 14400, "eoq": 1095, "orders_per_year": 13.2},
        ],
    )

    msg = response["result"]["mensagem"]
    assert "## Sensibilidade" in msg
    assert "| Cenário | Demanda anual | EOQ | Pedidos/ano |" in msg
    assert len(response.get("table_data", [])) == 3
