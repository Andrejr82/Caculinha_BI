from types import SimpleNamespace

from backend.app.api.v1.endpoints.chat import _is_chat_allowed_for_user
from backend.app.config.settings import settings


def _user(user_id: str, username: str, role: str):
    return SimpleNamespace(id=user_id, username=username, role=role)


def test_chat_canary_disabled_allows_any_user(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CANARY_ENABLED", False)
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_ROLES", "admin")
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_USERS", "")

    assert _is_chat_allowed_for_user(_user("u-1", "normal.user", "viewer")) is True


def test_chat_canary_enabled_blocks_user_outside_allowlist(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CANARY_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_ROLES", "admin")
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_USERS", "")

    assert _is_chat_allowed_for_user(_user("u-2", "normal.user", "viewer")) is False


def test_chat_canary_enabled_allows_user_by_role(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CANARY_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_ROLES", "admin,analyst")
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_USERS", "")

    assert _is_chat_allowed_for_user(_user("u-3", "ana.silva", "analyst")) is True


def test_chat_canary_enabled_allows_user_by_explicit_username(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CANARY_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_ROLES", "admin")
    monkeypatch.setattr(settings, "CHAT_CANARY_ALLOWED_USERS", "joao.teste")

    assert _is_chat_allowed_for_user(_user("u-4", "joao.teste", "viewer")) is True
