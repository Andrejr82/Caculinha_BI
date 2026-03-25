import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user
from backend.app.core.utils.session_manager import SessionManager


class MemoryUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.username = "memory-user"
        self.email = "memory@example.com"
        self.role = "analyst"
        self.is_active = True


def test_memory_endpoint_is_initialized_and_reads_chat_persistence(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    session_id = str(uuid.uuid4())
    current_user = MemoryUser()

    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    session_manager = SessionManager(
        storage_dir=str(tmp_path / "sessions"),
        db_path=str(db_path),
    )
    session_manager.add_message(
        session_id,
        "user",
        "Quero rever o histórico da análise de margem",
        current_user.id,
        metadata={"request_id": "req-user"},
    )
    session_manager.add_message(
        session_id,
        "assistant",
        "Resumo salvo na memória persistente.",
        current_user.id,
        metadata={"request_id": "req-assistant"},
    )

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            list_response = client.get("/api/v1/memory")
            assert list_response.status_code == 200
            listed = list_response.json()
            assert listed[0]["id"] == session_id
            assert listed[0]["message_count"] == 2

            detail_response = client.get(f"/api/v1/memory/{session_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["id"] == session_id
            assert detail["message_count"] == 2
            assert detail["messages"][1]["content"] == "Resumo salvo na memória persistente."
    finally:
        app.dependency_overrides.clear()
