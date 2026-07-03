import asyncio
import pytest
from comfylab.engine.locks import ResourceLockManager

@pytest.mark.asyncio
async def test_resource_lock_mutual_exclusion():
    manager = ResourceLockManager()
    address = "GPIB0::22::INSTR"
    shared_resource = []

    async def task_1():
        async with manager.acquire(address):
            shared_resource.append(1)
            await asyncio.sleep(0.1)
            shared_resource.append(2)

    async def task_2():
        async with manager.acquire(address):
            shared_resource.append(3)
            await asyncio.sleep(0.05)
            shared_resource.append(4)

    # Launch concurrently
    await asyncio.gather(task_1(), task_2())

    # Because task_1 acquired the lock first and slept for 0.1s, task_2 should wait.
    # Therefore, task_1 must complete (appending 1, 2) before task_2 can run (appending 3, 4).
    # Expected order: [1, 2, 3, 4]
    assert shared_resource == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_resource_lock_timeout():
    manager = ResourceLockManager()
    address = "GPIB0::22::INSTR"

    async def lock_holder():
        async with manager.acquire(address):
            await asyncio.sleep(0.5)

    async def lock_waiter():
        await asyncio.sleep(0.05)
        # Timeout is 0.1s, but holder sleeps 0.5s. This should raise TimeoutError.
        with pytest.raises(asyncio.TimeoutError):
            async with manager.acquire(address, timeout=0.1):
                pass

    await asyncio.gather(lock_holder(), lock_waiter())


@pytest.mark.asyncio
async def test_resource_lock_stats():
    manager = ResourceLockManager()
    address = "GPIB0::22::INSTR"

    # Acquire once
    async with manager.acquire(address):
        pass

    stats = manager.get_stats()
    assert stats["global"]["total_acquires"] == 1
    assert stats["global"]["contentions"] == 0
    assert stats["resources"][address]["acquires"] == 1
    assert stats["resources"][address]["contentions"] == 0

    # Cause a contention
    async def task_holder(event):
        async with manager.acquire(address):
            event.set()
            await asyncio.sleep(0.2)

    async def task_waiter(event):
        await event.wait()
        async with manager.acquire(address):
            pass

    event = asyncio.Event()
    await asyncio.gather(task_holder(event), task_waiter(event))

    stats2 = manager.get_stats()
    assert stats2["global"]["total_acquires"] == 3  # 1 (first) + 1 (holder) + 1 (waiter)
    assert stats2["global"]["contentions"] == 1
    assert stats2["resources"][address]["contentions"] == 1
