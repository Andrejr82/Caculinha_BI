from typing import Annotated, Dict, Any, List
from pathlib import Path
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.engine import make_url

from backend.app.api.dependencies import require_role
from backend.app.config.settings import settings
from backend.app.infrastructure.database.models import User
from backend.app.infrastructure.redis_client import get_sync_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


class DBConfig(BaseModel):
    use_sql_server: bool
    use_supabase: bool
    database_server: str | None
    database_name: str | None
    database_user: str | None
    supabase_url: str | None
    chat_state_backend: str | None = None
    database_driver: str | None = None


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    version: str | None = None
    tables: List[str] | None = None


def _is_chat_state_sqlserver_enabled() -> bool:
    return str(getattr(settings, "CHAT_STATE_BACKEND", "") or "").strip().lower() == "sqlserver"


def _database_runtime_mode() -> str:
    database_url = str(getattr(settings, "DATABASE_URL", "") or "").strip()
    if _is_chat_state_sqlserver_enabled() and database_url.startswith("mssql+pytds://"):
        return "sqlserver_pytds"
    if settings.USE_SQL_SERVER:
        return "sqlserver_async"
    if _is_chat_state_sqlserver_enabled():
        return "sqlserver_configured"
    return "sqlite"


def _redis_runtime_status() -> Dict[str, Any]:
    if not settings.REDIS_ENABLED:
        return {
            "status": "disabled",
            "required": settings.REDIS_REQUIRED,
            "message": "Redis disabled for this environment",
        }
    try:
        client = get_sync_redis_client()
        if client is None:
            return {
                "status": "unhealthy",
                "required": settings.REDIS_REQUIRED,
                "message": "Redis enabled but client not initialized",
            }
        client.ping()
        return {
            "status": "healthy",
            "required": settings.REDIS_REQUIRED,
            "message": "Redis connected",
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "required": settings.REDIS_REQUIRED,
            "message": str(exc),
        }


def _parse_database_config_from_url() -> Dict[str, str | None]:
    database_url = str(getattr(settings, "DATABASE_URL", "") or "").strip()
    if not database_url:
        return {
            "database_server": None,
            "database_name": None,
            "database_user": None,
            "database_driver": None,
        }

    try:
        url = make_url(database_url)
        return {
            "database_server": url.host,
            "database_name": url.database,
            "database_user": url.username,
            "database_driver": url.drivername,
        }
    except Exception as exc:
        logger.warning("Failed to parse DATABASE_URL: %s", exc)
        return {
            "database_server": None,
            "database_name": None,
            "database_user": None,
            "database_driver": None,
        }


def _test_connection_pytds() -> ConnectionTestResult:
    import pytds

    url = make_url(str(settings.DATABASE_URL))
    conn = pytds.connect(
        dsn=url.host,
        port=url.port or 1433,
        database=url.database,
        user=url.username,
        password=url.password,
        autocommit=True,
        cafile=None,
    )
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version_row = cursor.fetchone()
        version = version_row[0] if version_row else "Unknown"
        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        return ConnectionTestResult(
            success=True,
            message="Conexão pytds estabelecida com sucesso!",
            version=version.split("\n")[0] if version else None,
            tables=tables[:50],
        )
    finally:
        conn.close()

@router.get("/db-status")
async def get_db_status(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Status das conexões com banco de dados e arquivos.
    """
    parquet_path = Path(settings.PARQUET_DATA_PATH)
    parquet_status = "ok" if parquet_path.exists() else "missing"
    parquet_size = parquet_path.stat().st_size if parquet_path.exists() else 0
    parquet_path_used = str(parquet_path)

    return {
        "parquet": {
            "status": parquet_status,
            "analytics_source": "parquet",
            "size_mb": round(parquet_size / 1024 / 1024, 2) if parquet_size else 0,
            "path": parquet_path_used
        },
        "sql_server": {
            "status": "enabled" if (_is_chat_state_sqlserver_enabled() or settings.USE_SQL_SERVER) else "disabled",
            "url": settings.DATABASE_URL if (_is_chat_state_sqlserver_enabled() or settings.USE_SQL_SERVER) else None,
            "runtime_mode": _database_runtime_mode(),
            "chat_state_backend": settings.CHAT_STATE_BACKEND,
        },
        "redis": _redis_runtime_status(),
        "supabase": {
            "status": "enabled" if settings.USE_SUPABASE_AUTH else "disabled",
            "url": settings.SUPABASE_URL if settings.USE_SUPABASE_AUTH else None
        }
    }


@router.get("/config", response_model=DBConfig)
async def get_db_config(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Retorna as configurações detectadas do banco de dados.
    """
    parsed = _parse_database_config_from_url()

    return DBConfig(
        use_sql_server=settings.USE_SQL_SERVER or _is_chat_state_sqlserver_enabled(),
        use_supabase=settings.USE_SUPABASE_AUTH,
        database_server=parsed["database_server"],
        database_name=parsed["database_name"],
        database_user=parsed["database_user"],
        supabase_url=settings.SUPABASE_URL if settings.USE_SUPABASE_AUTH else None,
        chat_state_backend=settings.CHAT_STATE_BACKEND,
        database_driver=parsed["database_driver"],
    )


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_sql_connection(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Testa a conexão com o SQL Server e retorna versão e tabelas disponíveis.
    """
    runtime_mode = _database_runtime_mode()

    if runtime_mode == "sqlite":
        return ConnectionTestResult(
            success=False,
            message="SQL Server está desabilitado para este runtime"
        )

    try:
        if runtime_mode == "sqlserver_pytds":
            return await asyncio.wait_for(
                asyncio.to_thread(_test_connection_pytds),
                timeout=5.0,
            )

        if not settings.PYODBC_CONNECTION_STRING:
            return ConnectionTestResult(
                success=False,
                message="PYODBC_CONNECTION_STRING não configurado no .env"
            )

        import aioodbc

        async def _test_aioodbc():
            conn = await aioodbc.connect(dsn=settings.PYODBC_CONNECTION_STRING)
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT @@VERSION")
                    version_row = await cursor.fetchone()
                    version = version_row[0] if version_row else "Unknown"
                    await cursor.execute(
                        """
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                        """
                    )
                    tables_rows = await cursor.fetchall()
                    tables = [row[0] for row in tables_rows]
                return ConnectionTestResult(
                    success=True,
                    message="Conexão aioodbc estabelecida com sucesso!",
                    version=version.split("\n")[0] if version else None,
                    tables=tables[:50],
                )
            finally:
                await conn.close()

        return await asyncio.wait_for(_test_aioodbc(), timeout=5.0)

    except ImportError as e:
        return ConnectionTestResult(
            success=False,
            message=f"Bibliotecas necessárias não instaladas: {str(e)}"
        )
    except asyncio.TimeoutError:
        return ConnectionTestResult(
            success=False,
            message="Timeout ao conectar com SQL Server (5s)"
        )
    except Exception as e:
        logger.error(f"Error testing SQL connection: {e}", exc_info=True)
        return ConnectionTestResult(
            success=False,
            message=f"Erro inesperado: {str(e)}"
        )
