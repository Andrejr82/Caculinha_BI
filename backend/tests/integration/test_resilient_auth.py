import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user


class BrokenUser:
    """Simulates a partially broken profile object from auth/database drift."""

    def __init__(self, role: str = "user", allowed_segments=None):
        self.id = uuid.uuid4()
        self.username = "broken-user"
        self.email = None
        self.role = role
        self.is_active = True
        self.allowed_segments = allowed_segments
        self.last_login = None
        self.created_at = None
        self.updated_at = None

    @property
    def segments_list(self):
        # intentionally malformed input to exercise parser fallback
        if self.allowed_segments is None:
            return []
        if isinstance(self.allowed_segments, list):
            return self.allowed_segments
        return []


def test_auth_me_returns_200_with_broken_user_profile():
    async def _override_user():
        return BrokenUser(role="user", allowed_segments=None)

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "broken-user"
        assert "allowed_segments" in body
        assert isinstance(body["allowed_segments"], list)
    finally:
        app.dependency_overrides.clear()

