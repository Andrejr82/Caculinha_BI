from typing import Annotated, Dict, Any, List
from pathlib import Path
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import require_role
from app.config.settings import settings
from app.infrastructure.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


class DBConfig(BaseModel):
    use_sql_server: bool
    use_supabase: bool
    database_server: str | None
    database_name: str | None
    database_user: str | None
    supabase_url: str | None


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    version: str | None = None
    tables: List[str] | None = None

@router.get("/db-status")
async def get_db_status(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Status das conexões com banco de dados e arquivos.
    """
    # Verificar Parquet (Root Data vs Backend Data)
    # Backend usa logicamente: app/data/parquet OU ../../../../data/parquet
    
    # Vamos verificar ambos para reportar
    backend_parquet = Path("/app/data/parquet/admmat.parquet")
    local_parquet = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "data" / "parquet" / "admmat.parquet"
    
    parquet_status = "unknown"
    parquet_size = 0
    parquet_path_used = "none"
    
    if backend_parquet.exists():
        parquet_status = "ok"
        parquet_size = backend_parquet.stat().st_size
        parquet_path_used = str(backend_parquet)
    elif local_parquet.exists():
        parquet_status = "ok"
        parquet_size = local_parquet.stat().st_size
        parquet_path_used = str(local_parquet)
    else:
        parquet_status = "missing"

    return {
        "parquet": {
            "status": parquet_status,
            "size_mb": round(parquet_size / 1024 / 1024, 2) if parquet_size else 0,
            "path": parquet_path_used
        },
        "sql_server": {
            "status": "enabled" if settings.USE_SQL_SERVER else "disabled",
            "url": settings.DATABASE_URL if settings.USE_SQL_SERVER else None
        },
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
    # Extrair informações do DATABASE_URL se disponível
    db_server = None
    db_name = None
    db_user = None

    if settings.DATABASE_URL and settings.USE_SQL_SERVER:
        try:
            # Formato: mssql+aioodbc://user:pass@host:port/db?driver=...
            url_str = str(settings.DATABASE_URL)
            if "@" in url_str and "/" in url_str:
                # Extrair user
                user_part = url_str.split("://")[1].split(":")[0] if "://" in url_str else None
                # Extrair host
                host_part = url_str.split("@")[1].split("/")[0].split(":")[0] if "@" in url_str else None
                # Extrair database
                db_part = url_str.split("/")[-1].split("?")[0] if "/" in url_str else None

                db_user = user_part
                db_server = host_part
                db_name = db_part
        except Exception as e:
            logger.warning(f"Failed to parse DATABASE_URL: {e}")

    return DBConfig(
        use_sql_server=settings.USE_SQL_SERVER,
        use_supabase=settings.USE_SUPABASE_AUTH,
        database_server=db_server,
        database_name=db_name,
        database_user=db_user,
        supabase_url=settings.SUPABASE_URL if settings.USE_SUPABASE_AUTH else None
    )


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_sql_connection(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Testa a conexão com o SQL Server e retorna versão e tabelas disponíveis.
    """
    if not settings.USE_SQL_SERVER:
        return ConnectionTestResult(
            success=False,
            message="SQL Server está desabilitado (USE_SQL_SERVER=false)"
        )

    # Verificar se temos a connection string do pyodbc
    if not settings.PYODBC_CONNECTION_STRING:
        return ConnectionTestResult(
            success=False,
            message="PYODBC_CONNECTION_STRING não configurado no .env"
        )

    try:
        # Tentar importar o aioodbc e pyodbc
        import aioodbc
        import asyncio

        async def _test():
            try:
                # Criar conexão temporária usando a connection string ODBC
                conn = await asyncio.wait_for(
                    aioodbc.connect(dsn=settings.PYODBC_CONNECTION_STRING),
                    timeout=5.0
                )

                async with conn.cursor() as cursor:
                    # Obter versão do SQL Server
                    await cursor.execute("SELECT @@VERSION")
                    version_row = await cursor.fetchone()
                    version = version_row[0] if version_row else "Unknown"

                    # Listar tabelas
                    await cursor.execute("""
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                    """)
                    tables_rows = await cursor.fetchall()
                    tables = [row[0] for row in tables_rows]

                await conn.close()

                return ConnectionTestResult(
                    success=True,
                    message="Conexão estabelecida com sucesso!",
                    version=version.split('\n')[0] if version else None,
                    tables=tables[:50]  # Limitar a 50 tabelas
                )
            except asyncio.TimeoutError:
                return ConnectionTestResult(
                    success=False,
                    message="Timeout ao conectar com SQL Server (5s)"
                )
            except Exception as e:
                return ConnectionTestResult(
                    success=False,
                    message=f"Erro ao conectar: {str(e)}"
                )

        return await _test()

    except ImportError as e:
        return ConnectionTestResult(
            success=False,
            message=f"Bibliotecas necessárias não instaladas: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error testing SQL connection: {e}", exc_info=True)
        return ConnectionTestResult(
            success=False,
            message=f"Erro inesperado: {str(e)}"
        )
