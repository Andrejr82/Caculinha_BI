from backend.app.api.v1.endpoints.chat import (
    _build_guided_chat_query,
    _extract_semantic_chat_query,
    _parse_guided_action_param,
    _parse_playbook_context_param,
)
from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.app.core.utils.response_validator import validate_response


def test_parse_playbook_context_param_ignores_invalid_json() -> None:
    assert _parse_playbook_context_param("not-json") == {}


def test_parse_playbook_context_param_sanitizes_supported_fields() -> None:
    raw = '{"product":"Fita adesiva","segment":"Papelaria","une":"1685","period":"30 dias","objective":"Reposicao"}'

    assert _parse_playbook_context_param(raw) == {
        "product": "Fita adesiva",
        "segment": "Papelaria",
        "une": "1685",
        "period": "30 dias",
        "objective": "Reposicao",
    }


def test_parse_guided_action_param_sanitizes_supported_fields() -> None:
    raw = (
        '{"actionId":"critical_stock:plano_24h","actionLabel":"Plano 24h","source":"executive_cta",'
        '"playbookId":"critical_stock","prompt":"Plano operacional","directSend":true,'
        '"executionPolicy":"real_data_only","outputPreference":"operational_plan",'
        '"missingDataBehavior":"ask_minimum_required_inputs","toolHints":["encontrar_rupturas_criticas","consultar_dados_flexivel"]}'
    )

    assert _parse_guided_action_param(raw) == {
        "actionId": "critical_stock:plano_24h",
        "actionLabel": "Plano 24h",
        "source": "executive_cta",
        "playbookId": "critical_stock",
        "prompt": "Plano operacional",
        "directSend": True,
        "executionPolicy": "real_data_only",
        "outputPreference": "operational_plan",
        "missingDataBehavior": "ask_minimum_required_inputs",
        "toolHints": ["encontrar_rupturas_criticas", "consultar_dados_flexivel"],
    }


def test_build_guided_chat_query_injects_mode_and_context() -> None:
    query = _build_guided_chat_query(
        "onde esta a maior ruptura?",
        "critical_stock",
        {
            "product": "Fita adesiva",
            "segment": "Papelaria",
            "une": "1685",
            "period": "ultimos 30 dias",
            "objective": "priorizar reposicao",
        },
        {
            "actionLabel": "Plano 24h",
            "source": "executive_cta",
            "playbookId": "critical_stock",
            "directSend": True,
            "executionPolicy": "real_data_only",
            "outputPreference": "operational_plan",
            "missingDataBehavior": "ask_minimum_required_inputs",
            "toolHints": ["encontrar_rupturas_criticas", "consultar_dados_flexivel"],
        },
    )

    assert "Contexto operacional adicional para orientar esta resposta:" in query
    assert "- modo analitico: ruptura e reposicao" in query
    assert "- use apenas dados reais observados no sistema" in query
    assert "Diretrizes do modo:" in query
    assert "- priorize ruptura, cobertura de estoque e urgencia de reposicao" in query
    assert "- produto_foco: Fita adesiva" in query
    assert "- segmento_foco: Papelaria" in query
    assert "- lojas_ou_une: 1685" in query
    assert "- periodo: ultimos 30 dias" in query
    assert "- objetivo: priorizar reposicao" in query
    assert "Acao orientada:" in query
    assert "- acao: Plano 24h" in query
    assert "- politica_execucao: real_data_only" in query
    assert "- tools_sugeridas: encontrar_rupturas_criticas, consultar_dados_flexivel" in query
    assert "Pergunta do usuario:\nonde esta a maior ruptura?" in query


def test_extract_semantic_chat_query_returns_raw_user_question() -> None:
    query = _build_guided_chat_query(
        "Explique em linguagem simples a diferença entre faturamento, margem e giro de estoque.",
        None,
        {"period": "ultimos 30 dias"},
        None,
    )

    assert _extract_semantic_chat_query(query) == (
        "Explique em linguagem simples a diferença entre faturamento, margem e giro de estoque."
    )


def test_guided_wrapper_does_not_force_market_research_capability() -> None:
    service = object.__new__(ChatServiceV3)
    query = _build_guided_chat_query(
        "Compare papelaria entre as lojas 1685, 1974 e 2365 no último mês.",
        None,
        {"period": "ultimos 30 dias"},
        None,
    )

    assert service._query_expected_capability(query) == "data_query"


def test_guided_wrapper_does_not_block_plain_explanatory_response() -> None:
    service = object.__new__(ChatServiceV3)
    query = _build_guided_chat_query(
        "Explique em linguagem simples a diferença entre faturamento, margem e giro de estoque.",
        None,
        {"period": "ultimos 30 dias"},
        None,
    )
    response = {
        "type": "text",
        "result": {
            "mensagem": (
                "## Resumo executivo\n"
                "- Faturamento é o valor total vendido.\n\n"
                "## Tabela operacional\n"
                "- Margem mostra quanto sobra após custos e giro mede a velocidade de venda do estoque.\n\n"
                "## Próximas ações\n"
                "- Se quiser, eu exemplifico com números simples."
            )
        },
        "source": "llm.direct",
    }

    context = service._build_response_validation_context(query, response)
    validation = validate_response(response, query=query, context=context)

    assert validation.should_block is False
