from __future__ import annotations

from typing import Any

import structlog

from backend.app.config.settings import settings

logger = structlog.get_logger(__name__)

_redis_client: Any = None
_redis_sync_client: Any = None


async def init_redis_client() -> Any:
    global _redis_client, _redis_sync_client

    if not settings.REDIS_ENABLED:
        logger.info("redis_disabled")
        _redis_client = None
        _redis_sync_client = None
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as redis
    except ImportError as exc:
        logger.error("redis_dependency_missing", error=str(exc))
        if settings.REDIS_REQUIRED:
            raise RuntimeError("Redis is required but redis package is not installed") from exc
        return None

    try:
        import redis as redis_sync

        _redis_sync_client = redis_sync.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
        )
        _redis_sync_client.ping()
    except Exception as exc:
        logger.warning(
            "redis_sync_connection_failed",
            error=str(exc),
            redis_url=str(settings.REDIS_URL),
        )
        _redis_sync_client = None

    client = redis.from_url(
        str(settings.REDIS_URL),
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
    )

    try:
        await client.ping()
    except Exception as exc:
        logger.warning(
            "redis_connection_failed",
            error=str(exc),
            redis_url=str(settings.REDIS_URL),
            required=settings.REDIS_REQUIRED,
        )
        if settings.REDIS_REQUIRED:
            raise
        try:
            await client.aclose()
        except Exception:
            pass
        return None

    _redis_client = client
    logger.info(
        "redis_connected",
        redis_url=str(settings.REDIS_URL),
        key_prefix=settings.REDIS_KEY_PREFIX,
    )
    return _redis_client


def get_redis_client() -> Any:
    return _redis_client


def get_sync_redis_client() -> Any:
    return _redis_sync_client


async def close_redis_client() -> None:
    global _redis_client, _redis_sync_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:
            logger.warning("redis_close_failed", error=str(exc))
        finally:
            _redis_client = None
    if _redis_sync_client is not None:
        try:
            _redis_sync_client.close()
        except Exception as exc:
            logger.warning("redis_sync_close_failed", error=str(exc))
        finally:
            _redis_sync_client = None
