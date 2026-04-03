import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api import dependencies
from backend.app.api.middleware.auth import JWT_ALGORITHM, JWT_SECRET
from backend.app.api.v1.endpoints import chat as chat_endpoint
from backend.app.core.learning import continuous_learner as learner_module


client = TestClient(app)


class TraceLoggerRecorder:
    def __init__(self):
        self.events = []

    def info(self, event, **kwargs):
        self.events.append(("info", event, kwargs))

    def warning(self, event, **kwargs):
        self.events.append(("warning", event, kwargs))

    def error(self, event, **kwargs):
        self.events.append(("error", event, kwargs))


def _make_valid_token(role: str = "admin", username: str = "user@agentbi.com") -> str:
    return jwt.encode(
        {
            "sub": "12345678-1234-1234-1234-123456789012",
            "user_id": "12345678-1234-1234-1234-123456789012",
            "username": username,
            "email": username,
            "role": role,
            "tenant_id": "default",
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _collect_sse_events(response):
    data_events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            payload = line.replace("data: ", "")
            try:
                data_events.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
    return data_events


def _patch_chat_stream(monkeypatch, service):
    monkeypatch.setattr(chat_endpoint, "chat_service_v3", service, raising=False)
    monkeypatch.setattr(chat_endpoint, "cache_get", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(chat_endpoint, "cache_set", lambda *args, **kwargs: None, raising=False)


class _AutomationScalarsResult:
    def __init__(self, data):
        self._data = data

    def all(self):
        return self._data


class _AutomationExecuteResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return _AutomationScalarsResult(self._data)


class FakeAutomationDbSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        item.timestamp = datetime.utcnow()
        self.added.append(item)

    async def commit(self):
        return None

    async def execute(self, _query):
        return _AutomationExecuteResult(list(reversed(self.added)))


def test_stream_chat_rejects_legacy_query_token_for_chat():
    response = client.get("/api/v1/chat/stream?q=oi&session_id=s1&token=legacy")
    assert response.status_code == 401
    assert "stream token" in response.text.lower()


def test_stream_chat_accepts_valid_bearer_header():
    token = _make_valid_token()
    response = client.get(
        "/api/v1/chat/stream?q=oi&session_id=s1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")

    data_events = _collect_sse_events(response)
    assert any(evt.get("type") == "final" and evt.get("done") is True for evt in data_events)


def test_chat_capabilities_endpoint_returns_profile_matrix():
    token = _make_valid_token(role="viewer", username="viewer@agentbi.com")

    response = client.get(
        "/api/v1/chat/capabilities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "capabilities": {
            "memory": True,
            "multimodal": False,
            "attachments": False,
            "voice": False,
            "computer_use": False,
        },
        "role": "viewer",
        "subject": {
            "mode": "current_user",
            "user_id": "12345678-1234-1234-1234-123456789012",
            "username": "viewer@agentbi.com",
            "email": "viewer@agentbi.com",
        },
    }


def test_chat_capabilities_endpoint_supports_admin_debug_simulation():
    token = _make_valid_token(role="admin", username="admin@agentbi.com")

    response = client.get(
        "/api/v1/chat/capabilities?debug=true&role=viewer&username=pilot.viewer&email=pilot.viewer@example.com&user_id=pilot-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["capabilities"] == {
        "memory": True,
        "multimodal": False,
        "attachments": False,
        "voice": False,
        "computer_use": False,
    }
    assert body["subject"] == {
        "mode": "simulation",
        "user_id": "pilot-1",
        "username": "pilot.viewer",
        "email": "pilot.viewer@example.com",
    }
    assert body["diagnostics"]["attachments"]["missing_requires"] == ["multimodal"]
    assert body["diagnostics"]["voice"]["missing_requires"] == ["multimodal"]


def test_stream_chat_passes_resolved_capabilities_to_service(monkeypatch):
    token = _make_valid_token(role="viewer", username="viewer@agentbi.com")

    async def fake_process_message(*args, request_id=None, **kwargs):
        return {
            "type": "text",
            "result": {"mensagem": "Resposta com capability matrix."},
            "request_id": request_id,
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=fake_process_message))
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=quero um resumo&session_id=s-cap-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    process_kwargs = fake_service.process_message.await_args.kwargs
    assert process_kwargs["user_capabilities"] == {
        "memory": True,
        "multimodal": False,
        "attachments": False,
        "voice": False,
        "computer_use": False,
    }


def test_stream_chat_with_context_only_does_not_trigger_validation_block(monkeypatch):
    token = _make_valid_token()

    fake_service = SimpleNamespace(
        process_message=AsyncMock(
            return_value={
                "type": "text",
                "result": {
                    "mensagem": (
                        "## Resumo executivo\n"
                        "- Faturamento é o total vendido.\n\n"
                        "## Tabela operacional\n"
                        "- Margem é o ganho após custos e giro mede a velocidade de venda do estoque.\n\n"
                        "## Próximas ações\n"
                        "- Posso dar exemplos com números reais da base."
                    )
                },
                "source": "llm.direct",
                "mode": "deterministic_tool",
                "confidence": 0.88,
            }
        )
    )
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=Explique%20em%20linguagem%20simples%20a%20diferen%C3%A7a%20entre%20faturamento%2C%20margem%20e%20giro%20de%20estoque.&session_id=s-guided-ctx-1&playbook_context=%7B%22period%22%3A%22ultimos%2030%20dias%22%7D",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data_events = _collect_sse_events(response)
    final_event = next(evt for evt in data_events if evt.get("type") == "final")
    assert final_event["source"] == "llm.direct"
    assert final_event["mode"] == "deterministic_tool"
    assert "policy.response_validation" not in json.dumps(final_event, ensure_ascii=False)


def test_chat_history_requires_memory_capability():
    token = _make_valid_token(role="user", username="regular-user@example.com")

    response = client.get(
        "/api/v1/chat/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert "Memória persistente" in response.json()["detail"]


def test_stream_chat_final_event_includes_public_metadata(monkeypatch):
    token = _make_valid_token()

    fake_service = SimpleNamespace(
        process_message=AsyncMock(
            return_value={
                "type": "text",
                "result": {"mensagem": "Resposta com fontes."},
                "request_id": "req-stream-001",
                "source": "tool.pesquisar_mercado_web",
                "confidence": 0.88,
                "mode": "deterministic_tool",
                "citations": [{"source": "example", "url": "https://example.com"}],
            }
        )
    )

    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=consulta de vendas por segmento&session_id=s1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    final_event = next(evt for evt in data_events if evt.get("type") == "final")
    assert final_event["request_id"] == "req-stream-001"
    assert final_event["source"] == "tool.pesquisar_mercado_web"
    assert final_event["confidence"] == 0.88
    assert final_event["mode"] == "deterministic_tool"
    assert final_event["citations"] == [{"source": "example", "url": "https://example.com"}]


def test_stream_chat_emits_structured_trace_logs_for_request_and_async_job(monkeypatch):
    token = _make_valid_token()
    trace_recorder = TraceLoggerRecorder()

    async def fake_process_message(*args, request_id=None, **kwargs):
        return {
            "type": "text",
            "result": {"mensagem": "Resposta rastreável."},
            "request_id": request_id,
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=fake_process_message))
    _patch_chat_stream(monkeypatch, fake_service)
    monkeypatch.setattr(chat_endpoint, "trace_logger", trace_recorder, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=trace de sse&session_id=s-trace-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    events = [event for _, event, _ in trace_recorder.events]
    assert "chat_sse_stream_started" in events
    assert "chat_async_job_started" in events
    assert "chat_async_job_completed" in events
    assert "chat_sse_stream_finished" in events

    started_payload = next(payload for _, event, payload in trace_recorder.events if event == "chat_sse_stream_started")
    async_payload = next(payload for _, event, payload in trace_recorder.events if event == "chat_async_job_completed")
    finished_payload = next(payload for _, event, payload in trace_recorder.events if event == "chat_sse_stream_finished")

    assert async_payload["request_id"] == started_payload["request_id"]
    assert finished_payload["request_id"] == started_payload["request_id"]
    assert async_payload["job_name"] == "chat_service_process_message"


def test_stream_chat_contract_emits_progress_text_chart_table_and_final(monkeypatch):
    token = _make_valid_token()

    async def fake_process_message(*args, on_progress=None, **kwargs):
        if on_progress:
            await on_progress({"type": "tool_progress", "tool": "tool.data_query", "status": "start"})
            await on_progress({"type": "tool_progress", "tool": "tool.chart", "status": "executing"})
        return {
            "type": "text",
            "result": {"mensagem": "Analise com grafico e tabela pronta."},
            "request_id": "req-contract-001",
            "source": "tool.data_query",
            "chart_data": {
                "data": [{"type": "bar", "x": ["A"], "y": [10]}],
                "layout": {"title": "Teste"},
            },
            "table_data": [{"segmento": "A", "valor": 10}],
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=fake_process_message))
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=analise completa&session_id=s-contract-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    event_types = [evt.get("type") for evt in data_events]

    assert "tool_progress" in event_types
    assert "chart" in event_types
    assert "table" in event_types
    assert "text" in event_types
    assert "final" in event_types

    progress_event = next(evt for evt in data_events if evt.get("type") == "tool_progress")
    chart_event = next(evt for evt in data_events if evt.get("type") == "chart")
    table_event = next(evt for evt in data_events if evt.get("type") == "table")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert progress_event["tool"] == "tool.data_query"
    assert "chart_spec" in chart_event
    assert table_event["data"] == [{"segmento": "A", "valor": 10}]
    assert final_event["request_id"] == "req-contract-001"
    assert final_event["chart_spec"]["layout"]["title"] == "Teste"
    assert final_event["table_data"] == [{"segmento": "A", "valor": 10}]


def test_stream_chat_contract_emits_dashboard_and_final(monkeypatch):
    token = _make_valid_token()

    async def fake_process_message(*args, on_progress=None, **kwargs):
        if on_progress:
            await on_progress({"type": "tool_progress", "tool": "tool.dashboard", "status": "start"})
        return {
            "type": "dashboard",
            "result": {"mensagem": "Dashboard pronto."},
            "request_id": "req-dashboard-001",
            "dashboard_spec": {"title": "Painel Executivo", "widgets": []},
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=fake_process_message))
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=gere um dashboard&session_id=s-contract-2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    dashboard_event = next(evt for evt in data_events if evt.get("type") == "dashboard")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert dashboard_event["dashboard_spec"]["title"] == "Painel Executivo"
    assert final_event["request_id"] == "req-dashboard-001"
    assert final_event["dashboard_spec"]["title"] == "Painel Executivo"


def test_stream_chat_final_event_includes_image_asset(monkeypatch):
    token = _make_valid_token()

    fake_service = SimpleNamespace(
        process_message=AsyncMock(
            return_value={
                "type": "text",
                "result": {"mensagem": "Imagem pronta."},
                "request_id": "req-image-001",
                "image_asset": {
                    "url": "https://cdn.example.com/generated.png",
                    "alt": "Painel visual",
                },
                "mode": "image_generation",
            }
        )
    )

    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=gere uma imagem&session_id=s-image-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    final_event = next(evt for evt in data_events if evt.get("type") == "final")
    assert final_event["request_id"] == "req-image-001"
    assert final_event["image_asset"]["url"] == "https://cdn.example.com/generated.png"
    assert final_event["mode"] == "image_generation"


def test_stream_chat_contract_emits_keepalive_for_slow_agent(monkeypatch):
    token = _make_valid_token()

    async def slow_process_message(*args, **kwargs):
        await asyncio.sleep(0.03)
        return {
            "type": "text",
            "result": {"mensagem": "Resposta lenta, mas concluida."},
            "request_id": "req-keepalive-001",
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=slow_process_message))
    _patch_chat_stream(monkeypatch, fake_service)
    monkeypatch.setattr(chat_endpoint, "_SSE_EVENT_POLL_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(chat_endpoint, "_SSE_KEEPALIVE_INTERVAL_TICKS", 1, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=consulta demorada&session_id=s-contract-3",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    event_types = [evt.get("type") for evt in data_events]
    assert "keepalive" in event_types
    assert "final" in event_types


def test_stream_chat_timeout_for_generic_query_returns_safe_timeout_message(monkeypatch):
    token = _make_valid_token()

    async def timed_out_process_message(*args, **kwargs):
        raise asyncio.TimeoutError()

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=timed_out_process_message))
    _patch_chat_stream(monkeypatch, fake_service)
    monkeypatch.setattr(chat_endpoint, "_SSE_EVENT_POLL_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(chat_endpoint, "_SSE_KEEPALIVE_INTERVAL_TICKS", 1, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=quero uma analise detalhada de ruptura por categoria&session_id=s-timeout-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    text_response = "".join(evt.get("text", "") for evt in data_events if evt.get("type") == "text")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert any(evt.get("type") == "keepalive" for evt in data_events)
    assert "tempo limite de processamento foi excedido" in text_response.lower()
    assert final_event["done"] is True


def test_stream_chat_timeout_for_market_query_recovers_with_degraded_market_payload(monkeypatch):
    token = _make_valid_token()

    async def timed_out_process_message(*args, **kwargs):
        raise asyncio.TimeoutError()

    async def fake_market_recovery(*args, **kwargs):
        return {
            "text": "Recuperei a consulta de mercado em modo degradado.",
            "payload": {
                "source": "tool.pesquisar_precos_concorrentes",
                "confidence": 0.54,
                "mode": "deterministic_degraded_timeout",
                "citations": [{"source": "fallback_market", "url": "https://example.com/fallback"}],
            },
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=timed_out_process_message))
    _patch_chat_stream(monkeypatch, fake_service)
    monkeypatch.setattr(chat_endpoint, "_run_competitive_market_fast_path", fake_market_recovery, raising=False)
    monkeypatch.setattr(chat_endpoint, "_SSE_EVENT_POLL_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(chat_endpoint, "_SSE_KEEPALIVE_INTERVAL_TICKS", 1, raising=False)

    call_count = {"value": 0}

    def fake_is_market_query(_query):
        call_count["value"] += 1
        return call_count["value"] > 1

    monkeypatch.setattr(chat_endpoint, "_is_competitive_market_query", fake_is_market_query, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=pesquise preços concorrentes do arroz&session_id=s-timeout-market-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    text_response = "".join(evt.get("text", "") for evt in data_events if evt.get("type") == "text")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert "modo degradado" in text_response.lower()
    assert final_event["source"] == "tool.pesquisar_precos_concorrentes"
    assert final_event["confidence"] == 0.54
    assert final_event["mode"] == "deterministic_degraded_timeout"
    assert final_event["citations"] == [{"source": "fallback_market", "url": "https://example.com/fallback"}]


def test_stream_chat_recovers_from_agent_exception_with_safe_message(monkeypatch):
    token = _make_valid_token()

    async def broken_process_message(*args, **kwargs):
        raise RuntimeError("boom")

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=broken_process_message))
    _patch_chat_stream(monkeypatch, fake_service)
    monkeypatch.setattr(chat_endpoint, "_SSE_EVENT_POLL_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(chat_endpoint, "_SSE_KEEPALIVE_INTERVAL_TICKS", 1, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=explique a ruptura critica&session_id=s-error-recovery-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    text_response = "".join(evt.get("text", "") for evt in data_events if evt.get("type") == "text")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert "nao foi possivel concluir a analise agora" in text_response.lower()
    assert final_event["done"] is True


def test_stream_chat_contract_emits_error_and_final_when_service_unavailable(monkeypatch):
    token = _make_valid_token()

    async def fake_initialize():
        return None

    monkeypatch.setattr(chat_endpoint, "chat_service_v3", None, raising=False)
    monkeypatch.setattr(chat_endpoint, "initialize_agents_async", fake_initialize, raising=False)
    monkeypatch.setattr(chat_endpoint, "cache_get", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(chat_endpoint, "cache_set", lambda *args, **kwargs: None, raising=False)

    response = client.get(
        "/api/v1/chat/stream?q=consulta com erro&session_id=s-contract-4",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    error_event = next(evt for evt in data_events if evt.get("type") == "error")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert "could not be initialized" in error_event["error"]
    assert final_event["done"] is True


def test_post_chat_requires_valid_auth_token():
    response = client.post(
        "/api/v1/chat",
        json={"query": "teste"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_post_chat_uses_promotion_planner_for_operational_promotion_query():
    token = _make_valid_token()

    response = client.post(
        "/api/v1/chat",
        json={"query": "Como fazer uma promoção do EVA nas lojas 1685 e 2365 por 7 dias?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    full = body["full_agent_response"]
    assert full["source"] == "service.promotion_planner"
    assert full["mode"] == "promotion_planner"
    message = full["result"]["mensagem"]
    assert "## Plano promocional" in message
    assert "## Como executar" in message


def test_post_feedback_requires_valid_auth_token():
    response = client.post(
        "/api/v1/chat/feedback",
        json={"response_id": "r1", "feedback_type": "positive", "comment": "ok"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_post_chat_feedback_persists_structured_metadata_and_triggers_learning(monkeypatch, tmp_path):
    token = _make_valid_token()
    feedback_dir = tmp_path / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    fake_memory_agent = SimpleNamespace(save_feedback=AsyncMock(return_value=True))

    fake_learner = SimpleNamespace(
        process_interaction=AsyncMock(
            return_value={
                "actions_taken": ["added_to_golden_dataset"],
                "recommendations": [],
                "stats": {"total_processed": 1},
            }
        )
    )

    monkeypatch.setattr(chat_endpoint.settings, "LEARNING_FEEDBACK_PATH", str(feedback_dir), raising=False)
    monkeypatch.setattr(learner_module, "get_continuous_learner", lambda: fake_learner, raising=False)
    monkeypatch.setattr(chat_endpoint, "get_memory_agent", lambda: fake_memory_agent, raising=False)
    monkeypatch.setattr(
        chat_endpoint,
        "session_manager",
        SimpleNamespace(
            get_full_history=lambda session_id, user_id: [
                {
                    "role": "assistant",
                    "metadata": {
                        "request_id": "req-feedback-001",
                        "source": "tool.data_query",
                        "confidence": 0.91,
                        "mode": "deterministic_tool",
                        "citations": [{"source": "relatorio interno", "url": "https://example.com/relatorio"}],
                        "tool_names": ["consultar_dados_flexivel"],
                        "tool_call_count": 1,
                        "latency_seconds": 1.25,
                        "ab_variants": {
                            "prompt_variant": "concise",
                            "tool_routing_variant": "fast_fallback",
                            "ux_variant": "rich_progress",
                        },
                    },
                }
            ]
        ),
        raising=False,
    )

    payload = {
        "response_id": "req-feedback-001",
        "feedback_type": "positive",
        "comment": "Resposta útil",
        "session_id": "session-feedback-1",
        "query_text": "qual a venda por segmento",
        "response_text": "A venda do segmento A foi a maior.",
        "source": "tool.data_query",
        "confidence": 0.91,
        "mode": "deterministic_tool",
        "citations": [{"source": "relatorio interno", "url": "https://example.com/relatorio"}],
    }

    response = client.post(
        "/api/v1/chat/feedback",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "req-feedback-001"
    assert body["chat_state_feedback_status"] == "persisted"
    assert body["learning_status"] == "processed"
    assert body["learning_actions"] == ["added_to_golden_dataset"]

    feedback_file = Path(feedback_dir) / "feedback.jsonl"
    assert feedback_file.exists()

    lines = feedback_file.read_text(encoding="utf-8").strip().splitlines()
    saved_payload = json.loads(lines[-1])
    assert saved_payload["request_id"] == "req-feedback-001"
    assert saved_payload["response_id"] == "req-feedback-001"
    assert saved_payload["session_id"] == "session-feedback-1"
    assert saved_payload["source"] == "tool.data_query"
    assert saved_payload["citations_count"] == 1
    assert saved_payload["tool_names"] == ["consultar_dados_flexivel"]
    assert saved_payload["tool_call_count"] == 1
    assert saved_payload["latency_ms"] == 1250.0
    assert saved_payload["ab_variants"]["prompt_variant"] == "concise"

    fake_memory_agent.save_feedback.assert_awaited_once_with(
        request_id="req-feedback-001",
        rating=5,
        comment="Resposta útil",
    )
    fake_learner.process_interaction.assert_awaited_once()


def test_stream_chat_final_event_can_carry_automation_request(monkeypatch):
    token = _make_valid_token()

    fake_service = SimpleNamespace(
        process_message=AsyncMock(
            return_value={
                "type": "text",
                "result": {"mensagem": "Automação pronta para aprovação."},
                "request_id": "req-automation-stream-001",
                "source": "automation.registry",
                "confidence": 0.82,
                "mode": "automation_pending_approval",
                "automation_request": {
                    "proposal_id": "req-automation-stream-001",
                    "approval_status": "pending_user_approval",
                    "action": "spreadsheet.create_report",
                    "title": "Gerar planilha",
                    "summary": "Criar planilha exportável sob aprovação explícita.",
                },
            }
        )
    )
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=gere uma planilha&session_id=s-auto-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    final_event = next(evt for evt in _collect_sse_events(response) if evt.get("type") == "final")
    assert final_event["automation_request"]["action"] == "spreadsheet.create_report"
    assert final_event["automation_request"]["approval_status"] == "pending_user_approval"


def test_stream_chat_analytical_sales_report_query_emits_executive_sections_without_automation_request(monkeypatch):
    token = _make_valid_token()

    fake_service = SimpleNamespace(
        process_message=AsyncMock(
            return_value={
                "type": "text",
                "result": {
                    "mensagem": (
                        "## Resumo executivo\n"
                        "- O segmento Tecidos na UNE SCR foi consolidado no chat.\n\n"
                        "## Tabela operacional\n"
                        "| UNE | TOTAL_VENDAS |\n"
                        "|---|---|\n"
                        "| SCR | 125000 |\n\n"
                        "## Próximas ações\n"
                        "- Revisar mix e ruptura da UNE SCR nos próximos 7 dias."
                    )
                },
                "request_id": "req-analytical-report-stream-001",
                "source": "tool.consultar_dados_flexivel",
                "confidence": 0.91,
                "mode": "deterministic_tool",
                "table_data": [{"UNE": "SCR", "TOTAL_VENDAS": 125000}],
            }
        )
    )
    _patch_chat_stream(monkeypatch, fake_service)

    response = client.get(
        "/api/v1/chat/stream?q=gere%20um%20relat%C3%B3rio%20de%20vendas%20do%20segmento%20tecidos%20na%20une%20scr&session_id=s-analytical-report-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data_events = _collect_sse_events(response)
    text_response = "".join(evt.get("text", "") for evt in data_events if evt.get("type") == "text")
    table_event = next(evt for evt in data_events if evt.get("type") == "table")
    final_event = next(evt for evt in data_events if evt.get("type") == "final")

    assert "## Resumo executivo" in text_response
    assert "## Tabela operacional" in text_response
    assert "## Próximas ações" in text_response
    assert table_event["data"] == [{"UNE": "SCR", "TOTAL_VENDAS": 125000}]
    assert final_event["request_id"] == "req-analytical-report-stream-001"
    assert final_event["source"] == "tool.consultar_dados_flexivel"
    assert final_event["mode"] == "deterministic_tool"
    assert final_event["table_data"] == [{"UNE": "SCR", "TOTAL_VENDAS": 125000}]
    assert "automation_request" not in final_event


def test_chat_automation_endpoints_execute_reviewable_flow(monkeypatch, tmp_path):
    async def _override_user():
        return SimpleNamespace(
            id=uuid4(),
            username="admin",
            email="admin@agentbi.com",
            role="admin",
            is_active=True,
        )

    fake_db = FakeAutomationDbSession()

    async def _override_db():
        return fake_db

    from backend.app.services.chat_automation_service import ChatAutomationService

    monkeypatch.setattr(chat_endpoint.settings, "CHAT_CAPABILITY_COMPUTER_USE_ENABLED", True, raising=False)
    monkeypatch.setattr(chat_endpoint.settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES", "admin", raising=False)
    monkeypatch.setattr(chat_endpoint.settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS", "", raising=False)
    monkeypatch.setattr(chat_endpoint, "chat_service_v3", object(), raising=False)
    monkeypatch.setattr(
        chat_endpoint,
        "session_manager",
        SimpleNamespace(update_message_metadata_by_request_id=lambda **kwargs: True),
        raising=False,
    )
    monkeypatch.setattr(
        chat_endpoint,
        "chat_automation_service",
        ChatAutomationService(str(tmp_path)),
        raising=False,
    )

    app.dependency_overrides[dependencies.get_current_active_user] = _override_user
    app.dependency_overrides[chat_endpoint.get_db] = _override_db
    try:
        approve_response = client.post(
            "/api/v1/chat/automation/approve",
            json={
                "proposal": {
                    "proposal_id": "req-automation-http-001",
                    "action": "email.draft",
                    "title": "Preparar e-mail",
                    "summary": "Gerar rascunho revisável.",
                    "request_text": "Enviar e-mail com resumo executivo.",
                    "session_id": "session-auto-http-1",
                    "params": {
                        "recipient": "compras@empresa.com",
                        "subject": "Resumo executivo",
                        "body_context": "Resumo executivo do dia.",
                    },
                    "review_required": True,
                    "follow_up_action": "email.send",
                    "follow_up_label": "Enviar e-mail",
                }
            },
        )
        assert approve_response.status_code == 200
        first_state = approve_response.json()["automation"]
        assert first_state["approval_status"] == "draft_ready"
        assert first_state["draft"]["recipient"] == "compras@empresa.com"

        send_response = client.post(
            "/api/v1/chat/automation/approve",
            json={
                "approval_id": first_state["approval_id"],
                "follow_up_action": "email.send",
            },
        )
        assert send_response.status_code == 200
        final_state = send_response.json()["automation"]
        assert final_state["approval_status"] == "completed"
        assert final_state["artifact"]["filename"] == "email-outbox.json"

        history_response = client.get("/api/v1/chat/automation/history?limit=5")
        assert history_response.status_code == 200
        assert history_response.json()["items"][0]["approval_id"] == final_state["approval_id"]

        artifact_response = client.get(
            f"/api/v1/chat/automation/artifacts/{final_state['approval_id']}/{final_state['artifact']['filename']}"
        )
        assert artifact_response.status_code == 200
        assert artifact_response.headers["content-type"].startswith("application/json")
    finally:
        app.dependency_overrides.clear()


def test_chat_automation_endpoints_require_computer_use_capability(monkeypatch):
    async def _override_user():
        return SimpleNamespace(
            id=uuid4(),
            username="viewer",
            email="viewer@agentbi.com",
            role="viewer",
            is_active=True,
        )

    monkeypatch.setattr(chat_endpoint.settings, "CHAT_CAPABILITY_COMPUTER_USE_ENABLED", False, raising=False)
    app.dependency_overrides[dependencies.get_current_active_user] = _override_user
    try:
        response = client.post(
            "/api/v1/chat/automation/approve",
            json={
                "proposal": {
                    "proposal_id": "req-automation-http-403",
                    "action": "email.draft",
                    "title": "Preparar e-mail",
                    "summary": "Gerar rascunho revisável.",
                    "request_text": "Enviar e-mail com resumo executivo.",
                    "session_id": "session-auto-http-403",
                    "params": {"recipient": "compras@empresa.com"},
                }
            },
        )
        assert response.status_code == 403
        assert "Automações assistidas" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
