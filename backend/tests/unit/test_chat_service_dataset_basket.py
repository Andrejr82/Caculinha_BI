from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from backend.app.services.chat_service_v3 import ChatServiceV3


def test_dataset_basket_pipeline_uses_new_service() -> None:
    service = ChatServiceV3.__new__(ChatServiceV3)
    service.basket_analysis_service = Mock()
    service.basket_analysis_service.analyze.return_value = {
        "status": "unsupported",
        "analysis_mode": "unsupported",
        "parameters": {},
        "top_rules": [],
        "top_itemsets": [],
        "business_summary": [],
        "limitations": ["A base nao comprovou granularidade transacional."],
    }

    response = service._run_dataset_basket_pipeline("quais produtos comprados juntos na cesta?")

    assert response is not None
    assert response["source"] == "service.basket_analysis"
    assert response["mode"] == "dataset_basket_pipeline"
    service.basket_analysis_service.analyze.assert_called_once()


def test_response_matches_query_intent_rejects_basket_pipeline_for_visualization_query() -> None:
    service = ChatServiceV3.__new__(ChatServiceV3)

    assert service._response_matches_query_intent(
        "me gere um gráfico de vendas do produto 369947 em todas as lojas",
        {
            "source": "tool.minerar_cestas_frequentes",
            "mode": "attachment_basket_pipeline",
        },
    ) is False


def test_query_expected_capability_ignores_attachment_metadata_noise() -> None:
    service = ChatServiceV3.__new__(ChatServiceV3)

    capability = service._query_expected_capability(
        "me gere um gráfico de vendas do produto 369947 em todas as lojas\n\n"
        "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
    )

    assert capability == "visualization"


def test_response_capability_recognizes_chart_tool_source_without_chart_payload() -> None:
    service = ChatServiceV3.__new__(ChatServiceV3)

    capability = service._response_capability({"source": "tool.gerar_grafico_universal_v2"})

    assert capability == "visualization"
