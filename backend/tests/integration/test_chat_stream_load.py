import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.middleware.auth import JWT_ALGORITHM, JWT_SECRET
from backend.app.api.v1.endpoints import chat as chat_endpoint

client = TestClient(app)


def _make_valid_token(role: str = "admin", username: str = "load.user@agentbi.com") -> str:
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


def test_stream_chat_handles_parallel_requests_with_stable_p95(monkeypatch):
    token = _make_valid_token()

    async def fake_process_message(*args, request_id=None, **kwargs):
        return {
            "type": "text",
            "result": {"mensagem": "Carga estável validada."},
            "request_id": request_id,
        }

    fake_service = SimpleNamespace(process_message=AsyncMock(side_effect=fake_process_message))
    _patch_chat_stream(monkeypatch, fake_service)

    def execute_request(index: int):
        started_at = time.perf_counter()
        response = client.get(
            f"/api/v1/chat/stream?q=analise interna de margem index {index}&session_id=load-session-{index}",
            headers={"Authorization": f"Bearer {token}"},
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        events = _collect_sse_events(response)
        final_event = next(evt for evt in events if evt.get("type") == "final")
        return {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "request_id": final_event.get("request_id"),
            "done": final_event.get("done"),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(execute_request, range(20)))

    latencies = sorted(result["elapsed_ms"] for result in results)
    p95_index = max(0, math.ceil(len(latencies) * 0.95) - 1)
    p95_ms = latencies[p95_index]

    assert all(result["status_code"] == 200 for result in results)
    assert all(result["done"] is True for result in results)
    assert all(result["request_id"] for result in results)
    assert p95_ms < 2000, f"p95 muito alto para carga concorrente controlada: {p95_ms:.2f}ms"
