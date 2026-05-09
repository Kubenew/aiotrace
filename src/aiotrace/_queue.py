"""Queue context propagation for OpenTelemetry.

On Python < 3.9.17 / 3.10.7 / 3.11.1, ``Task.__step`` does not restore
the task's own context, so ``await queue.get()`` can resume the consumer
in the **producer's** context.  ``PropagatingQueue`` wraps each get/put
with proper token-based attach/detach to prevent context leaks.
"""

from __future__ import annotations

import asyncio
from typing import Any

from opentelemetry import context as otel_context


class PropagatingQueue(asyncio.Queue):
    """An ``asyncio.Queue`` that preserves OTEL context across ``get``/``put``.

    Captures the current OTEL context at call time and attaches it before
    awaiting the underlying operation.  The token is properly managed so
    context never leaks across nested queue operations.

    Usage is identical to ``asyncio.Queue``::

        queue = PropagatingQueue(maxsize=10)
        await queue.put(item)
        item = await queue.get()
    """

    async def get(self) -> Any:
        ctx = otel_context.get_current()
        token = otel_context.attach(ctx)
        try:
            return await super().get()
        finally:
            otel_context.detach(token)

    async def put(self, item: Any) -> None:
        ctx = otel_context.get_current()
        token = otel_context.attach(ctx)
        try:
            await super().put(item)
        finally:
            otel_context.detach(token)


def patch_queue() -> None:
    """Replace ``asyncio.Queue`` with ``PropagatingQueue`` globally."""
    asyncio.Queue = PropagatingQueue  # type: ignore[misc]
