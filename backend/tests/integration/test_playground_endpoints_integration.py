from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api import dependencies
from backend.app.api.v1.endpoints import playground as playground_endpoint


class FakeUser:
    def __init__(self, role: str = "user"):
        self.id = uuid.uuid4()
        self.username = "playground-user"
        self.email = "playground@example.com"
        self.role = role
        self.is_active = True
        self.allowed_segments = "[]"
        self.last_login = None
        self.created_at = None
        self.updated_at = None


class _ScalarsResult:
    def __init__(self, data):
        self._data = data

    def all(self):
        return self._data


class _ExecuteResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return _ScalarsResult(self._data)

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None


class FakeDbSession:
    def __init__(self):
        self.added = []
        self._execute_calls = 0

    async def execute(self, _query):
        self._execute_calls += 1
        now = datetime.utcnow()
        if self._execute_calls == 1:
            usage_logs = [
                SimpleNamespace(action="playground_chat_remote", details={"endpoint": "chat", "duration_ms": 120.0}, status="success", timestamp=now - timedelta(minutes=5)),
                SimpleNamespace(action="playground_stream_remote", details={"endpoint": "stream", "duration_ms": 250.0}, status="success", timestamp=now - timedelta(minutes=4)),
                SimpleNamespace(action="playground_stream_remote_error", details={"endpoint": "stream"}, status="error", timestamp=now - timedelta(minutes=3)),
            ]
            return _ExecuteResult(usage_logs)
        feedback_logs = [
            SimpleNamespace(details={"useful": True}),
            SimpleNamespace(details={"useful": False}),
        ]
        return _ExecuteResult(feedback_logs)

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        return None


@pytest.fixture
def client():
    return TestClient(app)


def test_playground_chat_returns_local_fallback_without_remote_key(client, monkeypatch):
    async def _override_user():
        return FakeUser(role="user")

    fake_db = FakeDbSession()

    async def _override_db():
        return fake_db

    async def _sql_access_state(_user, _db):
        return False, "Permissão não concedida.", None

    async def _remote_access(_user, _db):
        return False, "Canário desabilitado para este usuário."

    monkeypatch.setattr(playground_endpoint.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(playground_endpoint, "_get_sql_access_state", _sql_access_state)
    monkeypatch.setattr(playground_endpoint, "_resolve_remote_llm_access", _remote_access)
    app.dependency_overrides[dependencies.get_current_active_user] = _override_user
    app.dependency_overrides[playground_endpoint.get_db] = _override_db
    try:
        response = client.post("/api/v1/playground/chat", json={"message": "consulta qualquer", "history": [], "stream": False})
        assert response.status_code == 200
        body = response.json()
        assert body["model_info"]["model"] == "local-fallback"
        assert "request_id" in body["metadata"]
        assert body["metadata"]["source"] == "local-fallback"
    finally:
        app.dependency_overrides.clear()


def test_playground_stream_returns_sse_without_500(client, monkeypatch):
    async def _override_user():
        return FakeUser(role="user")

    fake_db = FakeDbSession()

    async def _override_db():
        return fake_db

    async def _sql_access_state(_user, _db):
        return False, "Permissão não concedida.", None

    async def _remote_access(_user, _db):
        return False, "Canário desabilitado para este usuário."

    monkeypatch.setattr(playground_endpoint.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(playground_endpoint, "_get_sql_access_state", _sql_access_state)
    monkeypatch.setattr(playground_endpoint, "_resolve_remote_llm_access", _remote_access)
    app.dependency_overrides[dependencies.get_current_active_user] = _override_user
    app.dependency_overrides[playground_endpoint.get_db] = _override_db
    try:
        response = client.post("/api/v1/playground/stream", json={"message": "consulta qualquer", "history": [], "stream": True})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        assert '"type": "done"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_playground_metrics_exposes_advanced_latency_and_error_rates(client):
    async def _override_admin():
        return FakeUser(role="admin")

    fake_db = FakeDbSession()

    async def _override_db():
        return fake_db

    app.dependency_overrides[dependencies.get_current_active_user] = _override_admin
    app.dependency_overrides[playground_endpoint.get_db] = _override_db
    try:
        response = client.get("/api/v1/playground/metrics")
        assert response.status_code == 200
        body = response.json()
        assert "latency_ms_p95" in body
        assert "latency_ms_p99" in body
        assert "error_rate_by_endpoint" in body
        assert "stream" in body["error_rate_by_endpoint"]
        assert body["total_requests"] >= 1
    finally:
        app.dependency_overrides.clear()
