"""Lock/Event/Semaphore context propagation for OpenTelemetry.

Same problem as Queue: when a coroutine is resumed after acquiring
a lock (or waiting on an event/semaphore), it may wake in the wrong
context on older Python versions.
"""

from __future__ import annotations

import asyncio

from opentelemetry import context as otel_context


class PropagatingLock(asyncio.Lock):
    """An ``asyncio.Lock`` that preserves OTEL context across ``acquire``."""

    async def acquire(self) -> bool:
        ctx = otel_context.get_current()
        result = await super().acquire()
        otel_context.attach(ctx)
        return result


class PropagatingEvent(asyncio.Event):
    """An ``asyncio.Event`` that preserves OTEL context across ``wait``."""

    async def wait(self) -> bool:
        ctx = otel_context.get_current()
        result = await super().wait()
        otel_context.attach(ctx)
        return result


class PropagatingSemaphore(asyncio.Semaphore):
    """An ``asyncio.Semaphore`` that preserves OTEL context across ``acquire``."""

    async def acquire(self) -> bool:
        ctx = otel_context.get_current()
        result = await super().acquire()
        otel_context.attach(ctx)
        return result


class PropagatingCondition(asyncio.Condition):
    """An ``asyncio.Condition`` that preserves OTEL context across ``wait``."""

    async def wait(self) -> bool:
        ctx = otel_context.get_current()
        result = await super().wait()
        otel_context.attach(ctx)
        return result


def patch_locks() -> None:
    """Replace stdlib synchronization primitives with propagating versions."""
    asyncio.Lock = PropagatingLock  # type: ignore[misc]
    asyncio.Event = PropagatingEvent  # type: ignore[misc]
    asyncio.Semaphore = PropagatingSemaphore  # type: ignore[misc]
    asyncio.Condition = PropagatingCondition  # type: ignore[misc]
