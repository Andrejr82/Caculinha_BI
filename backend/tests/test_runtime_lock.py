import asyncio

import pytest

from backend.app.infrastructure.runtime_lock import runtime_lock


@pytest.mark.asyncio
async def test_runtime_lock_local_fallback_serializes_access():
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    outcomes = []

    async def first_worker():
        async with runtime_lock("same-key", wait_timeout_seconds=0.5) as acquired:
            outcomes.append(("first", acquired))
            first_entered.set()
            await release_first.wait()

    async def second_worker():
        await first_entered.wait()
        async with runtime_lock("same-key", wait_timeout_seconds=0.1) as acquired:
            outcomes.append(("second", acquired))

    task1 = asyncio.create_task(first_worker())
    task2 = asyncio.create_task(second_worker())
    await asyncio.sleep(0.15)
    release_first.set()
    await asyncio.gather(task1, task2)

    assert ("first", True) in outcomes
    assert ("second", False) in outcomes
