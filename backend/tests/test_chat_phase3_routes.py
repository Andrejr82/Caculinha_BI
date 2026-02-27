from backend.main import app


def test_chat_phase3_routes_registered():
    paths = {route.path for route in app.router.routes}
    assert "/api/v1/chat/report-templates" in paths
    assert "/api/v1/chat/stream-token" in paths
    assert "/api/v1/chat/stream" in paths
