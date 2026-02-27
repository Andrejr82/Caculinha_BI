from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from backend.app.config.settings import settings


def probe_context7_url(base_url: str, timeout_sec: float = 1.5) -> Dict[str, Any]:
    """
    Probing leve de disponibilidade do endpoint Context7.

    Tenta HEAD e, em caso de falha por método, tenta GET.
    """
    if not base_url:
        return {"reachable": False, "http_status": None, "error": "base_url_missing"}

    for method in ("HEAD", "GET"):
        req = Request(base_url, method=method)
        try:
            with urlopen(req, timeout=timeout_sec) as resp:
                status = int(getattr(resp, "status", 200))
                return {
                    "reachable": 200 <= status < 500,
                    "http_status": status,
                    "error": None,
                    "probe_method": method,
                }
        except HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            # Se servidor respondeu 4xx/5xx, endpoint está vivo.
            if status:
                return {
                    "reachable": True,
                    "http_status": status,
                    "error": None,
                    "probe_method": method,
                }
        except URLError as exc:
            last_error = str(exc.reason)
        except Exception as exc:
            last_error = str(exc)
    return {
        "reachable": False,
        "http_status": None,
        "error": last_error if "last_error" in locals() else "probe_failed",
        "probe_method": None,
    }


def build_context7_status(
    *,
    enabled: bool,
    required: bool,
    base_url: Optional[str],
    timeout_sec: float,
    probe_func: Callable[[str, float], Dict[str, Any]] = probe_context7_url,
) -> Dict[str, Any]:
    """
    Constrói payload de status da integração Context7.
    """
    now = datetime.now(timezone.utc).isoformat()
    payload: Dict[str, Any] = {
        "service": "context7",
        "enabled": bool(enabled),
        "required": bool(required),
        "base_url": base_url,
        "timeout_sec": float(timeout_sec),
        "checked_at": now,
    }

    if not enabled:
        payload.update(
            {
                "state": "disabled",
                "reachable": False,
                "healthy": not required,
                "reason": "integration_disabled",
            }
        )
        return payload

    if not base_url:
        payload.update(
            {
                "state": "enabled_without_probe_target",
                "reachable": None,
                "healthy": not required,
                "reason": "base_url_not_configured",
            }
        )
        return payload

    probe = probe_func(base_url, timeout_sec)
    reachable = bool(probe.get("reachable"))
    payload.update(
        {
            "state": "enabled_probed",
            "reachable": reachable,
            "healthy": reachable or (not required),
            "probe": probe,
        }
    )
    return payload


def get_context7_status() -> Dict[str, Any]:
    """Status efetivo usando configurações do ambiente atual."""
    return build_context7_status(
        enabled=bool(getattr(settings, "CONTEXT7_ENABLED", False)),
        required=bool(getattr(settings, "CONTEXT7_REQUIRED", False)),
        base_url=getattr(settings, "CONTEXT7_BASE_URL", None),
        timeout_sec=float(getattr(settings, "CONTEXT7_TIMEOUT_SEC", 1.5)),
    )

