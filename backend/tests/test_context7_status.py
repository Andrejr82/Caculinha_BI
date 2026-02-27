from backend.app.core.integrations.context7_status import build_context7_status


def test_context7_disabled_not_required_is_healthy():
    result = build_context7_status(
        enabled=False,
        required=False,
        base_url=None,
        timeout_sec=1.5,
    )
    assert result["state"] == "disabled"
    assert result["healthy"] is True


def test_context7_disabled_required_is_unhealthy():
    result = build_context7_status(
        enabled=False,
        required=True,
        base_url=None,
        timeout_sec=1.5,
    )
    assert result["state"] == "disabled"
    assert result["healthy"] is False


def test_context7_enabled_without_base_url_required_is_unhealthy():
    result = build_context7_status(
        enabled=True,
        required=True,
        base_url=None,
        timeout_sec=1.5,
    )
    assert result["state"] == "enabled_without_probe_target"
    assert result["healthy"] is False


def test_context7_enabled_with_probe_success_is_healthy():
    def fake_probe(_url: str, _timeout: float):
        return {"reachable": True, "http_status": 200, "error": None}

    result = build_context7_status(
        enabled=True,
        required=True,
        base_url="http://context7.local/health",
        timeout_sec=1.5,
        probe_func=fake_probe,
    )
    assert result["state"] == "enabled_probed"
    assert result["reachable"] is True
    assert result["healthy"] is True


def test_context7_enabled_with_probe_failure_required_is_unhealthy():
    def fake_probe(_url: str, _timeout: float):
        return {"reachable": False, "http_status": None, "error": "timeout"}

    result = build_context7_status(
        enabled=True,
        required=True,
        base_url="http://context7.local/health",
        timeout_sec=1.5,
        probe_func=fake_probe,
    )
    assert result["state"] == "enabled_probed"
    assert result["reachable"] is False
    assert result["healthy"] is False

