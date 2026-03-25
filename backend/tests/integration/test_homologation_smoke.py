from unittest.mock import AsyncMock, Mock

import pytest

from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


def _build_service() -> ChatServiceV3:
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_homologation_smoke_simple_query():
    service = _build_service()
    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "A venda consolidada ficou estável no período analisado.",
            "source": "tool.consultar_dados_flexivel",
            "mode": "deterministic_tool",
            "confidence": 0.91,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="como estão as vendas por segmento?",
        session_id="smoke-simple",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "tool.consultar_dados_flexivel"
    assert response["mode"] == "deterministic_tool"
    assert "resumo executivo" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_homologation_smoke_chart_query():
    service = _build_service()
    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Segue o gráfico de vendas por loja.",
            "source": "tool.gerar_grafico_universal_v2",
            "mode": "deterministic_tool",
            "confidence": 0.94,
            "chart_data": {"type": "bar", "labels": ["1685"], "datasets": [{"data": [42]}]},
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me gere um gráfico de vendas por loja",
        session_id="smoke-chart",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "tool.gerar_grafico_universal_v2"
    assert response.get("chart_data")


@pytest.mark.asyncio
async def test_homologation_smoke_product_query():
    service = _build_service()
    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "O produto 369947 vende melhor nas UNEs 1685 e 2475.",
            "source": "tool.analisar_produto_todas_lojas",
            "mode": "deterministic_tool",
            "confidence": 0.92,
            "table_data": [
                {"une": "1685", "vendas": 120},
                {"une": "2475", "vendas": 97},
            ],
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="quais lojas vendem melhor o produto 369947?",
        session_id="smoke-product",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "tool.analisar_produto_todas_lojas"
    assert response["mode"] == "deterministic_tool"
    assert response.get("table_data")


@pytest.mark.asyncio
async def test_homologation_smoke_basket_query():
    service = _build_service()
    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Encontrei regras de associação relevantes na base transacional suportada.",
            "source": "service.basket_analysis",
            "mode": "dataset_basket_pipeline",
            "confidence": 0.76,
            "table_data": [
                {
                    "antecedente": ["COLA QUENTE"],
                    "consequente": ["TNT BRANCO"],
                    "support": 0.12,
                    "confidence": 0.88,
                    "lift": 5.9,
                }
            ],
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="quais produtos costumam ser comprados juntos?",
        session_id="smoke-basket",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "service.basket_analysis"
    assert response["mode"] == "dataset_basket_pipeline"
    assert response.get("table_data")
