from backend.app.core.playground_mode import (
    is_remote_llm_enabled,
    is_remote_llm_enabled_for_user,
    is_user_in_canary,
    mode_label,
)


def test_local_only_never_enables_remote():
    assert is_remote_llm_enabled("local_only", True) is False
    assert is_remote_llm_enabled("local_only", False) is False


def test_hybrid_optional_depends_on_key():
    assert is_remote_llm_enabled("hybrid_optional", True) is True
    assert is_remote_llm_enabled("hybrid_optional", False) is False


def test_remote_required_depends_on_key():
    assert is_remote_llm_enabled("remote_required", True) is True
    assert is_remote_llm_enabled("remote_required", False) is False


def test_unknown_mode_fails_safe_to_local():
    assert is_remote_llm_enabled("unexpected", True) is False
    assert mode_label("unexpected") == "Local only"


def test_user_in_canary_override_has_priority():
    assert (
        is_user_in_canary(
            user_id="123",
            username="ana",
            role="viewer",
            canary_enabled=True,
            allowed_roles_csv="admin",
            allowed_users_csv="",
            user_override=True,
        )
        is True
    )


def test_user_in_canary_by_role_or_username_or_id():
    assert (
        is_user_in_canary(
            user_id="123",
            username="ana",
            role="admin",
            canary_enabled=True,
            allowed_roles_csv="admin,user",
            allowed_users_csv="",
        )
        is True
    )
    assert (
        is_user_in_canary(
            user_id="123",
            username="fausto",
            role="viewer",
            canary_enabled=True,
            allowed_roles_csv="",
            allowed_users_csv="fausto",
        )
        is True
    )
    assert (
        is_user_in_canary(
            user_id="abc-uuid",
            username="lucas",
            role="viewer",
            canary_enabled=True,
            allowed_roles_csv="",
            allowed_users_csv="abc-uuid",
        )
        is True
    )


def test_user_in_canary_when_disabled_returns_true():
    assert (
        is_user_in_canary(
            user_id="123",
            username="ana",
            role="viewer",
            canary_enabled=False,
            allowed_roles_csv="",
            allowed_users_csv="",
        )
        is True
    )


def test_remote_llm_enabled_for_user_respects_canary_gate():
    assert (
        is_remote_llm_enabled_for_user(
            playground_mode="hybrid_optional",
            has_gemini_key=True,
            canary_enabled=True,
            user_in_canary=False,
        )
        is False
    )
    assert (
        is_remote_llm_enabled_for_user(
            playground_mode="hybrid_optional",
            has_gemini_key=True,
            canary_enabled=True,
            user_in_canary=True,
        )
        is True
    )
