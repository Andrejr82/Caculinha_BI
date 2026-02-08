"""
API Dependencies - Versão Final e Estável (DuckDB)
"""
from typing import Annotated, List, Optional
import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
import duckdb

from backend.app.config.database import get_db
# Use decode_token from middleware to match the JWT secret used in create_access_token
from backend.api.middleware.auth import decode_token
from backend.app.infrastructure.database.models import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

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
        return User(
            id=uuid.UUID(str(user_id)),
            username=payload.get("username", "user"),
            role=payload.get("role", "user"),
            allowed_segments=json.dumps(payload.get("allowed_segments", ["*"])),
            is_active=True
        )

    except Exception as e:
        logger.error(f"Erro de Autenticação: {e}")
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
                role="admin",
                allowed_segments=json.dumps(["*"]),
                is_active=True
            )

        with duckdb.connect(':memory:') as con:
            # Fix backslash for Windows
            safe_path = parquet_path.replace("\\", "/")
            res = con.execute(f"SELECT * FROM read_parquet('{safe_path}') WHERE id = '{user_id}'").fetchone()
            
            if not res:
                # Se não achou no parquet mas token é válido (ex: Supabase), tenta recuperar do token
                # Isso permite que usuários do Supabase usem o chat mesmo sem sync no parquet
                if payload.get("username"):
                     return User(
                        id=uuid.UUID(str(user_id)),
                        username=payload.get("username"),
                        role=payload.get("role", "user"),
                        allowed_segments=json.dumps(payload.get("allowed_segments", [])),
                        is_active=True
                    )
                raise HTTPException(status_code=401, detail="Usuário não encontrado")

            return User(
                id=uuid.UUID(str(res[0])),
                username=res[1],
                email=res[2] if len(res) > 2 else "",
                role=res[4] if len(res) > 4 else "user",
                allowed_segments=res[5] if len(res) > 5 else '["*"]',
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

# Admin-only check: role=admin OR username=user@agentbi.com
ADMIN_EMAIL = "user@agentbi.com"

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

