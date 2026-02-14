from __future__ import annotations


def is_remote_llm_enabled(playground_mode: str, has_gemini_key: bool) -> bool:
    mode = (playground_mode or "").strip().lower()
    if mode == "local_only":
        return False
    if mode == "hybrid_optional":
        return bool(has_gemini_key)
    if mode == "remote_required":
        return bool(has_gemini_key)
    # Fail-safe: unknown mode behaves as local only
    return False


def _parse_csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in str(value).split(",") if item.strip()}


def is_user_in_canary(
    *,
    user_id: str | None,
    username: str | None,
    role: str | None,
    canary_enabled: bool,
    allowed_roles_csv: str | None,
    allowed_users_csv: str | None,
    user_override: bool | None = None,
) -> bool:
    if user_override is not None:
        return user_override
    if not canary_enabled:
        return True

    allowed_roles = _parse_csv_set(allowed_roles_csv)
    allowed_users = _parse_csv_set(allowed_users_csv)

    if role and role.strip().lower() in allowed_roles:
        return True
    if user_id and str(user_id).strip().lower() in allowed_users:
        return True
    if username and str(username).strip().lower() in allowed_users:
        return True
    return False


def is_remote_llm_enabled_for_user(
    *,
    playground_mode: str,
    has_gemini_key: bool,
    canary_enabled: bool,
    user_in_canary: bool,
) -> bool:
    base_enabled = is_remote_llm_enabled(playground_mode, has_gemini_key)
    if not base_enabled:
        return False
    if not canary_enabled:
        return True
    return user_in_canary


def mode_label(playground_mode: str) -> str:
    mode = (playground_mode or "").strip().lower()
    if mode == "local_only":
        return "Local only"
    if mode == "hybrid_optional":
        return "Hybrid optional"
    if mode == "remote_required":
        return "Remote required"
    return "Local only"
