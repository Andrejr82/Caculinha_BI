from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any


def build_sql_access_context(*, expires_at: datetime | None) -> str:
    payload: dict[str, Any] = {}
    if expires_at is not None:
        dt = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
        payload["expires_at"] = dt.astimezone(timezone.utc).isoformat()
    return json.dumps(payload, ensure_ascii=False)


def parse_sql_access_context(context: str | None) -> dict[str, Any]:
    if not context:
        return {}
    try:
        data = json.loads(context)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def evaluate_sql_access(value: str | None, context: str | None, now: datetime | None = None) -> tuple[bool, str]:
    if str(value).lower() != "true":
        return False, "Permissão desabilitada."

    data = parse_sql_access_context(context)
    expires_at_raw = data.get("expires_at")
    if not expires_at_raw:
        return True, "Permissão ativa sem expiração."

    try:
        expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except Exception:
        return False, "Contexto de expiração inválido."

    check_time = now or datetime.now(timezone.utc)
    if check_time <= expires_at:
        return True, f"Permissão ativa até {expires_at.isoformat()}."
    return False, f"Permissão expirada em {expires_at.isoformat()}."
