from backend.app.core.utils.intent_classifier import IntentType, classify_intent
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.utils.response_validator import validate_response
from backend.app.core.utils.query_router import route_query
from backend.app.services.chat_service_v3 import ChatServiceV3


def _service() -> ChatServiceV3:
    return object.__new__(ChatServiceV3)


def test_compare_queries_no_longer_default_to_chart_capability() -> None:
    prompts = [
        "Compare as vendas da UNE 1685 nos últimos 30 dias com os 30 dias anteriores.",
        "Compare papelaria entre as lojas 1685, 1974 e 2365 no último mês.",
    ]
    service = _service()

    for prompt in prompts:
        result = classify_intent(prompt)
        assert result.intent == IntentType.ANALYSIS
        selection = route_query(result.intent, prompt, result.confidence)
        assert selection.tool_name == "consultar_dados_flexivel"
        assert service._query_expected_capability(prompt) == "data_query"


def test_discount_margin_prompt_is_calculation_and_sandbox_counts_as_calculation() -> None:
    prompt = "Se eu der 10% de desconto em um produto com margem atual de 28%, como fica a margem estimada?"
    result = classify_intent(prompt)
    assert result.intent == IntentType.CALCULATION

    response = {
        "source": "tool.calculation_sandbox",
        "mode": "deterministic_sandbox",
        "calculation": {"type": "margin_discount"},
        "table_data": [{"Indicador": "Margem estimada", "Valor": "20,0%"}],
    }
    assert ChatServiceV3._response_capability(response) == "calculation"


def test_cross_sell_query_does_not_trigger_market_basket_fast_path() -> None:
    service = _service()
    prompt = "Analise a cesta de compras de papelaria e sugira oportunidades de cross-sell."
    assert service._query_is_market_basket(prompt) is False


def test_business_combo_query_is_not_misclassified_as_small_talk() -> None:
    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    prompt = "Quais itens combinam com cola, tesoura e EVA em uma ação promocional?"
    assert agent._is_small_talk_query(prompt) is False


def test_combo_query_triggers_basket_pipeline_and_extracts_anchor_terms() -> None:
    service = _service()
    prompt = "Quais itens combinam com cola, tesoura e EVA em uma ação promocional?"
    assert service._query_is_market_basket(prompt) is True
    request = service._build_dataset_basket_request(prompt)
    assert request.target_terms == ["cola", "tesoura", "EVA"]


def test_basket_pipeline_response_does_not_flag_product_names_as_invalid_columns() -> None:
    response = {
        "source": "service.basket_analysis",
        "mode": "dataset_basket_pipeline",
        "result": {
            "mensagem": (
                "Resumo executivo: A associacao mais forte sugere EVA COLORIDO -> GLITTER POTE "
                "com lift 6.03 e confidence 90.68%."
            )
        },
        "table_data": [{"antecedent": ["EVA COLORIDO"], "consequent": ["GLITTER POTE"]}],
    }
    validation = validate_response(
        response,
        query="Quais itens combinam com cola, tesoura e EVA em uma ação promocional?",
        context={"mode": "dataset_basket_pipeline", "source": "service.basket_analysis", "expected_capability": "calculation"},
    )
    assert not any("colunas possivelmente inválidas" in issue for issue in validation.issues)
