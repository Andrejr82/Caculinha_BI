"""
API Dependencies - Versão Final e Estável (DuckDB)
"""
from typing import Annotated, List, Optional
import json
import uuid
import logging
from datetime import datetime, timezone
import time
from pathlib import Path

from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
import duckdb

from backend.app.config.database import get_db
# Use decode_token from middleware to match the JWT secret used in create_access_token
from backend.app.api.middleware.auth import decode_token
from backend.app.infrastructure.database.models import User

logger = logging.getLogger(__name__)
security = HTTPBearer()
ADMIN_EMAIL = "user@agentbi.com"

# Ephemeral stream token store (in-memory, short-lived, limited reuse)
_STREAM_TOKENS: dict[str, tuple[str, float, int]] = {}
_STREAM_TOKEN_TTL_SECONDS = 120
_STREAM_TOKEN_MAX_USES = 3


def _fallback_segments_for_role(role: str) -> list[str]:
    return ["*"] if role == "admin" else []


def _normalize_allowed_segments(raw_value, role: str) -> list[str]:
    """Normalize allowed_segments from JWT/parquet payloads with role-aware fallback."""
    fallback = _fallback_segments_for_role(role)
    if raw_value is None:
        return fallback

    if isinstance(raw_value, str):
        value = raw_value.strip()
        if not value:
            return fallback
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()] or fallback
        return fallback

    if isinstance(raw_value, list):
        normalized = [str(item) for item in raw_value if str(item).strip()]
        return normalized or fallback

    return fallback


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        return token or None
    return None


async def get_token_from_header_or_query(
    request: Request,
    token: str | None = Query(default=None),
    stream_token: str | None = Query(default=None),
) -> str:
    """
    Hybrid token extraction for SSE:
    1) Authorization Bearer header
    2) Query parameter token (only for approved SSE endpoints)
    """
    header_token = _extract_bearer_token(request)
    if header_token:
        return header_token

    sse_query_allowlist = {
        "/api/v1/code-chat/stream",
        "/api/v1/playground/stream",
        "/api/v2/code-chat/stream",
        "/api/v2/playground/stream",
    }
    chat_stream_paths = {"/api/v1/chat/stream", "/api/v2/chat/stream"}

    if request.url.path in chat_stream_paths:
        if stream_token:
            resolved = consume_stream_token(stream_token)
            if resolved:
                return resolved
        raise HTTPException(status_code=401, detail="Missing or invalid stream token")

    if request.url.path in sse_query_allowlist and token:
        return token

    raise HTTPException(status_code=401, detail="Missing authentication token")


def issue_stream_token(
    access_token: str,
    ttl_seconds: int = _STREAM_TOKEN_TTL_SECONDS,
    max_uses: int = _STREAM_TOKEN_MAX_USES
) -> str:
    """Create a short-lived opaque token that maps to the JWT for SSE URLs."""
    now = time.time()
    # Cleanup expired tokens opportunistically
    expired = [k for k, (_, exp, _) in _STREAM_TOKENS.items() if exp <= now]
    for k in expired:
        _STREAM_TOKENS.pop(k, None)

    opaque = str(uuid.uuid4())
    _STREAM_TOKENS[opaque] = (access_token, now + ttl_seconds, max_uses)
    return opaque


def consume_stream_token(opaque_token: str) -> str | None:
    """Resolve and consume one use of a stream token (short-lived, limited reuse)."""
    entry = _STREAM_TOKENS.get(opaque_token)
    if not entry:
        return None
    access_token, expires_at, remaining_uses = entry
    if time.time() > expires_at:
        _STREAM_TOKENS.pop(opaque_token, None)
        return None
    if remaining_uses <= 0:
        _STREAM_TOKENS.pop(opaque_token, None)
        return None

    remaining_uses -= 1
    if remaining_uses <= 0:
        _STREAM_TOKENS.pop(opaque_token, None)
    else:
        _STREAM_TOKENS[opaque_token] = (access_token, expires_at, remaining_uses)
    return access_token

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """
    Autenticação via Supabase - usa dados do JWT diretamente.
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Supabase Auth: usar dados do token JWT diretamente
        user_metadata = payload.get("user_metadata", {}) or {}
        token_role = str(payload.get("role", "")).strip().lower()
        metadata_role = str(user_metadata.get("role", "")).strip().lower()
        email = payload.get("email") or user_metadata.get("email")
        username = payload.get("username") or payload.get("email", "user").split('@')[0]
        if (email or "").lower() == ADMIN_EMAIL or (username or "").lower() == ADMIN_EMAIL:
            role = "admin"
        elif token_role and token_role not in {"authenticated", "anon"}:
            role = token_role
        elif metadata_role:
            role = metadata_role
        else:
            role = "user"
        raw_allowed_segments = payload.get("allowed_segments", user_metadata.get("allowed_segments"))
        allowed_segments = _normalize_allowed_segments(raw_allowed_segments, role)

        return User(
            id=uuid.UUID(str(user_id)),
            username=username,
            email=email,
            role=role,
            allowed_segments=json.dumps(allowed_segments),
            is_active=True
        )

    except Exception as e:
        import traceback
        try:
            with open("auth_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now()}] Auth Error: {str(e)}\n")
                f.write(f"Token (part): {token[:10] if token else 'None'}...\n")
                f.write(f"Traceback: {traceback.format_exc()}\n")
        except:
            pass # Fail silently if logging fails
            
        logger.error(f"Erro de Autenticação por Token: {e}")
        raise HTTPException(status_code=401, detail="Não autorizado")

async def get_current_user_from_token(token: str) -> User:
    """
    Autentica usuário a partir de token string (usado para SSE/WebSockets)
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Caminho dos dados - Resolução Robusta
        base_dir = Path(__file__).parent.parent.parent.parent # Root
        possible_paths = [
            Path("/app/app/data/parquet/users.parquet"), # Docker absolute
            base_dir / "backend" / "data" / "parquet" / "users.parquet",
            base_dir / "data" / "parquet" / "users.parquet",
            base_dir / "backend" / "app" / "data" / "parquet" / "users.parquet"
        ]
        
        parquet_path = str(possible_paths[2]) # Default fallback (root/data)
        for p in possible_paths:
            if p.exists():
                parquet_path = str(p)
                break

        # Fallback Admin Emergencial
        if payload.get("username") == "admin":
             return User(
                id=uuid.UUID(str(user_id)),
                username="admin",
                email=payload.get("email"),
                role="admin",
                allowed_segments=json.dumps(["*"]),
                is_active=True
            )

        # Check parquet existence before querying
        res = None
        if Path(parquet_path).exists():
            try:
                with duckdb.connect(':memory:') as con:
                    # Fix backslash for Windows
                    safe_path = parquet_path.replace("\\", "/")
                    res = con.execute(f"SELECT * FROM read_parquet('{safe_path}') WHERE id = '{user_id}'").fetchone()
            except Exception as e:
                logger.warning(f"Failed to query Parquet for user {user_id}: {e}")
                res = None
        else:
             logger.warning(f"users.parquet not found at {parquet_path}. Fallback to token payload.")

        # Always return User if we have valid payload, regardless of Parquet result
        # This ensures Supabase users work even without local sync
        user_metadata = payload.get("user_metadata", {})
        token_role = str(payload.get("role", "")).strip().lower()
        metadata_role = str(user_metadata.get("role", "")).strip().lower()
        email = payload.get("email") or user_metadata.get("email")
        username = payload.get("username") or payload.get("email", "user").split('@')[0]
        if (email or "").lower() == ADMIN_EMAIL or (username or "").lower() == ADMIN_EMAIL:
            role = "admin"
        elif token_role and token_role not in {"authenticated", "anon"}:
            role = token_role
        elif metadata_role:
            role = metadata_role
        else:
            role = "user"
        allowed_segments = _normalize_allowed_segments(
            payload.get("allowed_segments") or user_metadata.get("allowed_segments"),
            role,
        )
        
        return User(
            id=uuid.UUID(str(user_id)),
            username=username,
            email=email,
            role=role,
            allowed_segments=json.dumps(allowed_segments),
            is_active=True
        )

    except Exception as e:
        logger.error(f"Erro de Autenticação por Token: {e}")
        raise HTTPException(status_code=401, detail="Não autorizado")

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    return current_user

def require_role(*allowed_roles: str):
    async def role_checker(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return user
    return role_checker

def require_permission(permission: str):
    async def perm_checker(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if user.role == "admin": return user
        return user
    return perm_checker

async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Require admin access: role=admin OR email=user@agentbi.com
    Returns 403 Forbidden for non-admin users.
    """
    is_admin = (
        current_user.role == "admin" or 
        current_user.username == ADMIN_EMAIL or
        getattr(current_user, 'email', '') == ADMIN_EMAIL
    )
    if not is_admin:
        logger.warning(f"Admin access denied for user: {current_user.username}")
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user

