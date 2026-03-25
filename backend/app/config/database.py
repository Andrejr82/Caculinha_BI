"""
Database Configuration
SQLAlchemy async engine and session
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from backend.app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Create async engine with optimized pool settings.
# Local fallback note:
# `mssql+pytds://` is supported for chat state local fallback, but it is a
# synchronous dialect. In this module we keep the generic async DB dependency
# on SQLite unless the configured SQL Server URL is async-capable.
database_url = str(settings.DATABASE_URL or "")
use_async_sqlserver = (
    settings.USE_SQL_SERVER
    and bool(database_url)
    and not database_url.startswith("mssql+pytds://")
)

if use_async_sqlserver:
    engine = create_async_engine(
        database_url,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_timeout=settings.SQL_SERVER_TIMEOUT,
        connect_args={"timeout": settings.SQL_SERVER_TIMEOUT},
    )
else:
    # Use explicit runtime SQLite path for local/dev persistence only.
    sqlite_path = Path(settings.CHAT_STATE_DB_PATH)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Using SQLite database: %s", sqlite_path)

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{sqlite_path}",
        poolclass=NullPool,
        echo=False,
    )

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all models"""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
