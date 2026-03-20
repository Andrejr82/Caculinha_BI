import pytest
from unittest.mock import Mock, AsyncMock, patch

import backend.app.services.chat_service_v3 as chat_service_module
from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.app.core.utils.session_manager import SessionManager
from backend.services.metrics import MetricsService


class TraceLoggerRecorder:
    def __init__(self):
        self.events = []

    def info(self, event, **kwargs):
        self.events.append(("info", event, kwargs))

    def warning(self, event, **kwargs):
        self.events.append(("warning", event, kwargs))

    def error(self, event, **kwargs):
        self.events.append(("error", event, kwargs))


@pytest.fixture(autouse=True)
def reset_metrics_state():
    metrics = MetricsService()
    metrics.reset()
    ChatServiceV3._reset_role_rate_limit_state()
    yield
    metrics.reset()
    ChatServiceV3._reset_role_rate_limit_state()


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
    assert metrics.get_counter("chat_ab_bucket_total", labels={"experiment": "prompt_variant", "variant": "control"}) + metrics.get_counter("chat_ab_bucket_total", labels={"experiment": "prompt_variant", "variant": "concise"}) == 1

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


@pytest.mark.asyncio
async def test_process_message_records_semantic_quality_metrics_and_request_id():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(
        return_value={
            "response": "Pesquisa de mercado concluída com fontes.",
            "source": "tool.pesquisar_mercado_web",
            "citations": [{"source": "example", "url": "https://example.com"}],
            "mode": "deterministic_tool",
        }
    )

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        result = await service.process_message(
            query="faça uma pesquisa de mercado de caderno universitário",
            session_id="s3",
            user_id="u3",
            user_role="analyst",
            request_id="req-semantic-001",
        )

    assert result["request_id"] == "req-semantic-001"

    metrics = MetricsService()
    assert metrics.get_counter("tool_selection_accuracy_total") == 1
    assert metrics.get_counter("tool_selection_accuracy_hits_total") == 1
    assert metrics.get_gauge("tool_selection_accuracy") == 1.0

    assert metrics.get_counter("citation_coverage_total") == 1
    assert metrics.get_counter("citation_coverage_hits_total") == 1
    assert metrics.get_gauge("citation_coverage") == 1.0


@pytest.mark.asyncio
async def test_process_message_exposes_public_metadata_for_frontend_contract():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(
        return_value={
            "response": "Pesquisa fundamentada concluída.",
            "source": "tool.pesquisar_mercado_web",
            "confidence": 0.82,
            "citations": [{"source": "example", "url": "https://example.com"}],
            "mode": "deterministic_tool",
        }
    )

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        result = await service.process_message(
            query="faça uma pesquisa de mercado de caneta azul",
            session_id="s-meta",
            user_id="u-meta",
            user_role="analyst",
            request_id="req-meta-001",
        )

    assert result["request_id"] == "req-meta-001"
    assert result["source"] == "tool.pesquisar_mercado_web"
    assert result["confidence"] == 0.82
    assert result["mode"] == "deterministic_tool"
    assert result["citations"] == [{"source": "example", "url": "https://example.com"}]
    assert isinstance(result["ab_variants"], dict)
    assert set(result["ab_variants"].keys()) == {"prompt_variant", "tool_routing_variant", "ux_variant"}
    assert "_internal_meta" not in result


@pytest.mark.asyncio
async def test_process_message_enforces_role_rate_limit(monkeypatch):
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(return_value={"response": "ok"})

    monkeypatch.setattr(service, "_get_role_rate_limit_per_minute", lambda _role: 1)

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        first = await service.process_message(
            query="consulta 1",
            session_id="s4",
            user_id="u4",
            user_role="viewer",
            request_id="req-rate-001",
        )
        second = await service.process_message(
            query="consulta 2",
            session_id="s4",
            user_id="u4",
            user_role="viewer",
            request_id="req-rate-002",
        )

    assert first["request_id"] == "req-rate-001"
    assert second["request_id"] == "req-rate-002"
    assert "Limite de solicitações excedido" in second["result"]["mensagem"]

    metrics = MetricsService()
    assert metrics.get_counter("chat_rate_limited_total") == 1
    assert metrics.get_counter("chat_rate_limited_total", labels={"role": "viewer"}) == 1


@pytest.mark.asyncio
async def test_process_message_emits_structured_trace_logs(monkeypatch):
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []
    session_manager.add_message = Mock()

    service = ChatServiceV3(session_manager=session_manager)
    service._index_memory_message = AsyncMock()

    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(
        return_value={
            "response": "Resposta rastreável pronta.",
            "tool_calls": ["consultar_dados_flexivel"],
            "source": "tool.data_query",
            "mode": "deterministic_tool",
        }
    )
    trace_recorder = TraceLoggerRecorder()
    on_progress = AsyncMock()

    monkeypatch.setattr(chat_service_module, "trace_logger", trace_recorder, raising=False)

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent):
        result = await service.process_message(
            query="traga a venda por segmento",
            session_id="s-trace",
            user_id="u-trace",
            user_role="analyst",
            request_id="req-trace-001",
            on_progress=on_progress,
        )

    assert result["request_id"] == "req-trace-001"

    events = [event for _, event, _ in trace_recorder.events]
    assert "chat_request_started" in events
    assert "chat_tool_progress" in events
    assert "chat_tool_trace" in events
    assert "chat_async_job_started" in events
    assert "chat_async_job_completed" in events
    assert "chat_request_finished" in events

    tool_trace_payload = next(payload for _, event, payload in trace_recorder.events if event == "chat_tool_trace")
    assert tool_trace_payload["request_id"] == "req-trace-001"
    assert "consultar_dados_flexivel" in tool_trace_payload["tool_names"]

    async_job_payload = next(payload for _, event, payload in trace_recorder.events if event == "chat_async_job_completed")
    assert async_job_payload["job_name"] == "conversation_memory_index"
