from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog

from backend.app.config.settings import settings
from backend.app.infrastructure.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

_LOCAL_LOCKS: dict[str, asyncio.Lock] = {}
_LOCAL_LOCKS_GUARD = asyncio.Lock()


async def _get_local_lock(lock_key: str) -> asyncio.Lock:
    async with _LOCAL_LOCKS_GUARD:
        lock = _LOCAL_LOCKS.get(lock_key)
        if lock is None:
            lock = asyncio.Lock()
            _LOCAL_LOCKS[lock_key] = lock
        return lock


@asynccontextmanager
async def runtime_lock(
    lock_key: str,
    *,
    ttl_seconds: int = 30,
    wait_timeout_seconds: float = 3.0,
) -> AsyncIterator[bool]:
    redis_client = get_redis_client()
    namespaced_key = f"{settings.REDIS_KEY_PREFIX}:runtime_lock:{lock_key}"

    if redis_client is not None:
        token = uuid.uuid4().hex
        deadline = time.monotonic() + max(0.1, wait_timeout_seconds)
        acquired = False
        while time.monotonic() < deadline:
            try:
                acquired = bool(
                    await redis_client.set(
                        namespaced_key,
                        token,
                        ex=max(1, ttl_seconds),
                        nx=True,
                    )
                )
            except Exception as exc:
                logger.warning("redis_runtime_lock_failed_falling_back_to_local", error=str(exc), lock_key=lock_key)
                break
            if acquired:
                break
            await asyncio.sleep(0.05)

        if acquired:
            try:
                yield True
            finally:
                try:
                    current_token = await redis_client.get(namespaced_key)
                    if current_token == token:
                        await redis_client.delete(namespaced_key)
                except Exception as exc:
                    logger.warning("redis_runtime_lock_release_failed", error=str(exc), lock_key=lock_key)
            return

    lock = await _get_local_lock(lock_key)
    try:
        await asyncio.wait_for(lock.acquire(), timeout=max(0.1, wait_timeout_seconds))
    except asyncio.TimeoutError:
        yield False
        return

    try:
        yield True
    finally:
        if lock.locked():
            lock.release()
