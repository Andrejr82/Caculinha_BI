from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent


def _agent_stub() -> CaculinhaBIAgent:
    return CaculinhaBIAgent.__new__(CaculinhaBIAgent)


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
    assert "Top grupos críticos" in msg
    assert "Evidência:" in msg
    assert "GRUPO A" in msg
