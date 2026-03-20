import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user
from backend.app.api.v1.endpoints import chat as chat_endpoint
from backend.app.core.utils.session_manager import SessionManager


class StubUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.username = "history-user"
        self.email = "history@example.com"
        self.role = "analyst"
        self.is_active = True


def test_chat_history_endpoint_returns_persisted_session_and_sessions(tmp_path):
    session_manager = SessionManager(
        storage_dir=str(tmp_path / "sessions"),
        db_path=str(tmp_path / "agentbi.db"),
    )
    current_user = StubUser()
    session_id = str(uuid.uuid4())

    session_manager.add_message(
        session_id,
        "user",
        "Quero revisar sell-out do item 123",
        current_user.id,
        metadata={"request_id": "req-user"},
    )
    session_manager.add_message(
        session_id,
        "assistant",
        "Aqui está o resumo por loja.",
        current_user.id,
        metadata={
            "request_id": "req-assistant",
            "source": "tool.consultar_dados_flexivel",
            "ui_payload": {
                "type": "table",
                "request_id": "req-assistant",
                "data": [{"une": "1685", "sell_out": 91}],
            },
        },
    )

    async def _override_user():
        return current_user

    original_session_manager = chat_endpoint.session_manager
    app.dependency_overrides[get_current_active_user] = _override_user
    chat_endpoint.session_manager = session_manager

    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/chat/history?session_id={session_id}")
        assert response.status_code == 200

        body = response.json()
        assert body["session_id"] == session_id
        assert len(body["items"]) == 2
        assert body["items"][1]["metadata"]["request_id"] == "req-assistant"
        assert body["sessions"][0]["id"] == session_id
        assert body["sessions"][0]["message_count"] == 2

        delete_response = client.delete(f"/api/v1/chat/history/{session_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        reloaded = client.get(f"/api/v1/chat/history?session_id={session_id}")
        assert reloaded.status_code == 200
        reloaded_body = reloaded.json()
        assert reloaded_body["items"] == []
        assert reloaded_body["sessions"] == []
    finally:
        app.dependency_overrides.clear()
        chat_endpoint.session_manager = original_session_manager
