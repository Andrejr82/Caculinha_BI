import json
from datetime import datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.middleware.auth import JWT_ALGORITHM, JWT_SECRET


client = TestClient(app)


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

    data_events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            payload = line.replace("data: ", "")
            try:
                data_events.append(json.loads(payload))
            except json.JSONDecodeError:
                continue

    assert any(evt.get("type") == "final" and evt.get("done") is True for evt in data_events)


def test_post_chat_requires_valid_auth_token():
    response = client.post(
        "/api/v1/chat",
        json={"query": "teste"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_post_feedback_requires_valid_auth_token():
    response = client.post(
        "/api/v1/chat/feedback",
        json={"response_id": "r1", "feedback_type": "positive", "comment": "ok"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
