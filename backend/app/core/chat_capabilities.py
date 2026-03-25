from typing import Any, Dict, Tuple

from fastapi import HTTPException, status

from backend.app.config.settings import settings

_CAPABILITY_CONFIG = {
    "memory": {
        "enabled": "CHAT_CAPABILITY_MEMORY_ENABLED",
        "roles": "CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES",
        "users": "CHAT_CAPABILITY_MEMORY_ALLOWED_USERS",
        "detail": "Memória persistente não habilitada para este perfil.",
    },
    "multimodal": {
        "enabled": "CHAT_CAPABILITY_MULTIMODAL_ENABLED",
        "roles": "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES",
        "users": "CHAT_CAPABILITY_MULTIMODAL_ALLOWED_USERS",
        "detail": "Recursos multimodais não habilitados para este perfil.",
    },
    "attachments": {
        "enabled": "CHAT_CAPABILITY_ATTACHMENTS_ENABLED",
        "roles": "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES",
        "users": "CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS",
        "detail": "Anexos e ingestão de arquivos não habilitados para este perfil.",
        "requires": ("multimodal",),
    },
    "voice": {
        "enabled": "CHAT_CAPABILITY_VOICE_ENABLED",
        "roles": "CHAT_CAPABILITY_VOICE_ALLOWED_ROLES",
        "users": "CHAT_CAPABILITY_VOICE_ALLOWED_USERS",
        "detail": "Recursos de voz não habilitados para este perfil.",
        "requires": ("multimodal",),
    },
    "computer_use": {
        "enabled": "CHAT_CAPABILITY_COMPUTER_USE_ENABLED",
        "roles": "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES",
        "users": "CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS",
        "detail": "Automações assistidas não habilitadas para este perfil.",
    },
}


def get_chat_capabilities_for_user(user: Any) -> Dict[str, bool]:
    resolved, _ = resolve_chat_capabilities_for_user(user)
    return resolved


def get_chat_capability_diagnostics_for_user(user: Any) -> Dict[str, Dict[str, Any]]:
    _, diagnostics = resolve_chat_capabilities_for_user(user)
    return diagnostics


def resolve_chat_capabilities_for_user(user: Any) -> Tuple[Dict[str, bool], Dict[str, Dict[str, Any]]]:
    role = str(getattr(user, "role", "") or "").strip().lower()
    user_refs = _collect_user_refs(user)

    resolved: Dict[str, bool] = {}
    diagnostics: Dict[str, Dict[str, Any]] = {}
    for capability, config in _CAPABILITY_CONFIG.items():
        enabled = bool(getattr(settings, config["enabled"], False))
        allowed_roles = _parse_csv(getattr(settings, config["roles"], ""))
        allowed_users = _parse_csv(getattr(settings, config["users"], ""))
        allowed_by_role = role in allowed_roles
        allowed_by_user = bool(user_refs.intersection(allowed_users))
        base_allowed = enabled and (allowed_by_role or allowed_by_user)
        requires = tuple(str(item) for item in (config.get("requires") or ()))
        missing_requires = [
            parent_capability
            for parent_capability in requires
            if not resolved.get(parent_capability, False)
        ]

        resolved[capability] = base_allowed and not missing_requires
        diagnostics[capability] = {
            "enabled": enabled,
            "allowed_by_role": allowed_by_role,
            "allowed_by_user": allowed_by_user,
            "requires": list(requires),
            "missing_requires": missing_requires,
            "active": resolved[capability],
        }
    return resolved, diagnostics


def require_chat_capability(user: Any, capability: str) -> None:
    if get_chat_capabilities_for_user(user).get(capability):
        return
    detail = _CAPABILITY_CONFIG.get(capability, {}).get("detail") or "Capacidade não habilitada para este perfil."
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _parse_csv(raw_value: Any) -> set[str]:
    return {
        item.strip().lower()
        for item in str(raw_value or "").split(",")
        if item.strip()
    }


def _collect_user_refs(user: Any) -> set[str]:
    refs = {
        str(getattr(user, "id", "") or "").strip().lower(),
        str(getattr(user, "username", "") or "").strip().lower(),
        str(getattr(user, "email", "") or "").strip().lower(),
    }
    refs.discard("")
    return refs
