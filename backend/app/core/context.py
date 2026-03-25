from contextvars import ContextVar
from typing import Optional, List
import sys
from backend.app.infrastructure.database.models import User

# Namespace compatibility: avoid duplicated module state under "app.*" vs "backend.app.*"
_THIS_MODULE = sys.modules[__name__]
sys.modules["app.core.context"] = _THIS_MODULE
sys.modules["backend.app.core.context"] = _THIS_MODULE

# Context variable to hold the current user for the request duration
_current_user_context: ContextVar[Optional[User]] = ContextVar("current_user_context", default=None)

def set_current_user_context(user: User):
    """Set the user for the current request context."""
    _current_user_context.set(user)

def get_current_user_context() -> Optional[User]:
    """Get the user from the current request context."""
    return _current_user_context.get()

def get_current_user_segments() -> List[str]:
    """Get allowed segments for the current user safely."""
    user = get_current_user_context()
    if not user:
        return []

    role = str(getattr(user, "role", "") or "").strip().lower()
    segments = []

    raw_segments = getattr(user, "segments_list", None)
    if isinstance(raw_segments, list):
        segments = [str(s).strip() for s in raw_segments if str(s).strip()]
    elif raw_segments:
        segments = [str(raw_segments).strip()]

    if not segments:
        raw_allowed = getattr(user, "allowed_segments", None)
        if isinstance(raw_allowed, list):
            segments = [str(s).strip() for s in raw_allowed if str(s).strip()]
        elif isinstance(raw_allowed, str):
            value = raw_allowed.strip()
            if value:
                if value.startswith("[") and value.endswith("]"):
                    try:
                        import json

                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            segments = [str(s).strip() for s in parsed if str(s).strip()]
                    except Exception:
                        segments = [value]
                else:
                    segments = [value]

    # Admin or full access
    if role == "admin" or "*" in segments:
        return ["*"]

    return segments
