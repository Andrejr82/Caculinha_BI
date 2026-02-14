from datetime import datetime, timedelta, timezone

from backend.app.core.playground_sql_access import build_sql_access_context, evaluate_sql_access


def test_sql_access_without_expiration_is_active():
    context = build_sql_access_context(expires_at=None)
    active, _ = evaluate_sql_access("true", context)
    assert active is True


def test_sql_access_with_future_expiration_is_active():
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    context = build_sql_access_context(expires_at=expires_at)
    active, _ = evaluate_sql_access("true", context)
    assert active is True


def test_sql_access_with_past_expiration_is_inactive():
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    context = build_sql_access_context(expires_at=expires_at)
    active, reason = evaluate_sql_access("true", context)
    assert active is False
    assert "expirada" in reason.lower()
