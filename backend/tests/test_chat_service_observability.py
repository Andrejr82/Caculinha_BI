import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.app.core.utils.session_manager import SessionManager
from backend.services.metrics import MetricsService


@pytest.fixture(autouse=True)
def reset_metrics_state():
    metrics = MetricsService()
    metrics.reset()
    yield
    metrics.reset()


@pytest.mark.asyncio
async def test_process_message_records_observability_metrics_on_success():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(
        return_value={
            "response": "Resposta com gráfico pronta",
            "tool_calls": [
                {"function": {"name": "gerar_grafico_universal_v2"}},
                "consultar_dados_flexivel",
            ],
        }
    )

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        result = await service.process_message(
            query="gere um gráfico de vendas por segmento",
            session_id="s1",
            user_id="u1",
            user_role="analyst",
        )

    assert result["type"] == "text"
    assert "mensagem" in result["result"]

    metrics = MetricsService()
    assert metrics.get_counter("chat_requests_total") == 1
    assert metrics.get_counter("chat_errors_total") == 0
    assert metrics.get_counter("chat_tool_calls_total") == 2
    assert metrics.get_counter("chat_tokens_in_total") > 0
    assert metrics.get_counter("chat_tokens_out_total") > 0

    latency = metrics.get_histogram_stats("chat_latency_seconds")
    complex_latency = metrics.get_histogram_stats("chat_latency_seconds", labels={"complexity": "complex"})
    assert latency.get("count", 0) >= 1
    assert complex_latency.get("count", 0) >= 1


@pytest.mark.asyncio
async def test_process_message_records_error_metrics_on_exception():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(side_effect=RuntimeError("falha controlada"))

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        result = await service.process_message(
            query="consulta simples de vendas",
            session_id="s2",
            user_id="u2",
            user_role="viewer",
        )

    assert result["type"] == "text"
    assert "Erro ao processar" in result["result"]["mensagem"]

    metrics = MetricsService()
    assert metrics.get_counter("chat_requests_total") == 1
    assert metrics.get_counter("chat_errors_total") == 1

    latency = metrics.get_histogram_stats("chat_latency_seconds")
    simple_latency = metrics.get_histogram_stats("chat_latency_seconds", labels={"complexity": "simple"})
    assert latency.get("count", 0) >= 1
    assert simple_latency.get("count", 0) >= 1
