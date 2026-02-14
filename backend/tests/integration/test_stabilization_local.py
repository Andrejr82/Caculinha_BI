import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api import dependencies
from backend.app.api.v1.endpoints import chat as chat_endpoint
from backend.app.api.v1.endpoints import code_chat as code_chat_endpoint
from backend.app.api.v1.endpoints import playground as playground_endpoint
from backend.app.api.dependencies import get_current_active_user
from backend.app.core.llm_gemini_adapter import GeminiLLMAdapter


class FakeUser:
    def __init__(self, role: str = "user", allowed_segments=None):
        self.id = uuid.uuid4()
        self.username = "local-user"
        self.email = None
        self.role = role
        self.is_active = True
        self.allowed_segments = "[]"
        self.last_login = None
        self.created_at = None
        self.updated_at = None
        self._segments = allowed_segments

    @property
    def segments_list(self):
        return self._segments if self._segments is not None else []


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_me_shape_and_types(client):
    async def _override_user():
        return FakeUser(role="user", allowed_segments=[])

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["email"] is None
        assert body["created_at"] is None
        assert body["updated_at"] is None
        assert body["allowed_segments"] == []
    finally:
        app.dependency_overrides.clear()


def test_chat_stream_query_token_allows_user(client, monkeypatch):
    async def _token_user(_token: str):
        return FakeUser(role="user", allowed_segments=["PAPELARIA"])

    class _FakeChatService:
        async def process_message(self, query, session_id, user_id, on_progress=None):
            return {"type": "text", "result": {"mensagem": f"ok: {query}"}}

    monkeypatch.setattr(dependencies, "get_current_user_from_token", _token_user)
    monkeypatch.setattr(chat_endpoint, "chat_service_v3", _FakeChatService())

    response = client.get("/api/v1/chat/stream?q=teste&token=fake-token&session_id=session-x")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    text_body = response.text
    assert '"type": "text"' in text_body
    assert '"done": true' in text_body.lower()


def test_code_chat_stream_query_token_allows_user_or_degrades(client, monkeypatch):
    # Non-admin must be forbidden.
    async def _non_admin(_token: str):
        return FakeUser(role="user")

    monkeypatch.setattr(dependencies, "get_current_user_from_token", _non_admin)
    forbidden_response = client.get("/api/v1/code-chat/stream?q=x&token=fake")
    assert forbidden_response.status_code == 403

    # Admin with missing index should degrade with actionable message.
    async def _admin(_token: str):
        return FakeUser(role="admin", allowed_segments=["*"])

    monkeypatch.setattr(dependencies, "get_current_user_from_token", _admin)
    monkeypatch.setattr(code_chat_endpoint, "get_code_rag_service", lambda: (_ for _ in ()).throw(Exception("index missing")))
    degraded_response = client.get("/api/v1/code-chat/stream?q=x&token=fake")
    assert degraded_response.status_code == 200
    assert "index missing; run scripts/index_codebase.py" in degraded_response.text


def test_llm_rate_limit_degrades_fast(monkeypatch):
    class _FakeModel:
        def generate_content(self, contents, request_options=None):
            raise Exception("429 quota exceeded retry in 1s")

    class _FakeGenAI:
        @staticmethod
        def configure(api_key=None):
            return None

        class GenerationConfig:
            def __init__(self, **kwargs):
                pass

        class GenerativeModel:
            def __init__(self, **kwargs):
                self._model = _FakeModel()

            def generate_content(self, contents, request_options=None):
                return self._model.generate_content(contents, request_options=request_options)

    import backend.app.core.llm_gemini_adapter as gemini_module

    monkeypatch.setattr(gemini_module, "GEMINI_AVAILABLE", True)
    monkeypatch.setattr(gemini_module, "genai", _FakeGenAI)

    adapter = GeminiLLMAdapter(model_name="gemini-2.5-pro", gemini_api_key="local-test-key")
    start = time.perf_counter()
    result = adapter.get_completion([{"role": "user", "content": "test"}])
    elapsed = time.perf_counter() - start

    assert elapsed < 5
    assert "error" in result


def test_no_hardcoded_model_strings():
    # Settings remains source of truth; runtime pages/endpoints should not hardcode old Gemini ids.
    files = [
        Path("backend/app/api/v1/endpoints/playground.py"),
        Path("frontend-solid/src/pages/Playground.tsx"),
    ]
    forbidden = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-exp"]

    for file_path in files:
        content = file_path.read_text(encoding="utf-8")
        for bad in forbidden:
            assert bad not in content, f"{bad} found in {file_path}"


def test_playground_stream_degrades_instead_of_500(client, monkeypatch):
    async def _active_user():
        return FakeUser(role="admin", allowed_segments=["*"])

    class _BrokenAdapter:
        def __init__(self, *args, **kwargs):
            raise Exception("429 RESOURCE_EXHAUSTED quota")

    app.dependency_overrides[get_current_active_user] = _active_user
    monkeypatch.setattr(playground_endpoint, "GeminiLLMAdapter", _BrokenAdapter)
    try:
        response = client.post(
            "/api/v1/playground/stream",
            json={"message": "teste", "history": [], "stream": True},
        )
        assert response.status_code == 200
        body = response.text
        assert '"type": "degraded"' in body or '"type": "error"' in body
    finally:
        app.dependency_overrides.clear()
