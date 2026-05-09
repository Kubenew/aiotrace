"""Queue context propagation for OpenTelemetry.

On Python < 3.9.17 / 3.10.7 / 3.11.1, ``Task.__step`` does not restore
the task's own context, so ``await queue.get()`` can resume the consumer
in the **producer's** context.  ``PropagatingQueue`` re-attaches the
consumer's OTEL context after every resume, fixing span nesting.
"""

from __future__ import annotations

import asyncio
from typing import Any

from opentelemetry import context as otel_context


class PropagatingQueue(asyncio.Queue):
    """An ``asyncio.Queue`` that preserves OTEL context across ``get``/``put``.

    Usage is identical to ``asyncio.Queue``::

        queue = PropagatingQueue(maxsize=10)
        await queue.put(item)
        item = await queue.get()
    """

    async def get(self) -> Any:
        ctx = otel_context.get_current()
        item = await super().get()
        otel_context.attach(ctx)
        return item

    async def put(self, item: Any) -> None:
        ctx = otel_context.get_current()
        await super().put(item)
        otel_context.attach(ctx)


def patch_queue() -> None:
    """Replace ``asyncio.Queue`` with ``PropagatingQueue`` globally."""
    asyncio.Queue = PropagatingQueue  # type: ignore[misc]
