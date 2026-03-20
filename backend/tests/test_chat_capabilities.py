from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.config.settings import settings
from backend.app.core.chat_capabilities import (
    get_chat_capabilities_for_user,
    require_chat_capability,
)


def _make_user(
    *,
    role: str = "user",
    user_id: str = "user-1",
    username: str = "user1",
    email: str = "user1@example.com",
):
    return SimpleNamespace(
        id=user_id,
        username=username,
        email=email,
        role=role,
    )


def test_get_chat_capabilities_resolves_role_matrix(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES", "admin,viewer")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES", "admin,analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES", "admin,analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_ROLES", "admin,analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ENABLED", False)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES", "admin")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS", "")

    capabilities = get_chat_capabilities_for_user(_make_user(role="viewer"))

    assert capabilities == {
        "memory": True,
        "multimodal": False,
        "attachments": False,
        "voice": False,
        "computer_use": False,
    }


def test_get_chat_capabilities_accepts_user_override(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ENABLED", False)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_USERS", "special@example.com")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS", "special@example.com")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_USERS", "special@example.com")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS", "special@example.com")

    capabilities = get_chat_capabilities_for_user(
        _make_user(role="user", username="special", email="special@example.com")
    )

    assert capabilities["memory"] is False
    assert capabilities["multimodal"] is True
    assert capabilities["attachments"] is True
    assert capabilities["voice"] is True
    assert capabilities["computer_use"] is True


def test_child_capabilities_follow_multimodal_master_switch(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ENABLED", False)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES", "analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES", "analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_ROLES", "analyst")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_VOICE_ALLOWED_USERS", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ENABLED", False)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES", "")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS", "")

    capabilities = get_chat_capabilities_for_user(_make_user(role="analyst"))

    assert capabilities["multimodal"] is False
    assert capabilities["attachments"] is False
    assert capabilities["voice"] is False


def test_require_chat_capability_raises_for_blocked_profile(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ENABLED", True)
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES", "admin")
    monkeypatch.setattr(settings, "CHAT_CAPABILITY_MEMORY_ALLOWED_USERS", "")

    with pytest.raises(HTTPException) as exc_info:
        require_chat_capability(_make_user(role="viewer"), "memory")

    assert exc_info.value.status_code == 403
    assert "Memória persistente" in exc_info.value.detail
