"""TaskGroup context propagation for OpenTelemetry.

:func:`asyncio.TaskGroup` (Python 3.11+)  creates child tasks via
``loop.create_task``.  If the loop-level method has not been patched,
the child tasks may inherit a stale context.

This module provides ``PropagatingTaskGroup`` which explicitly captures
the OTEL context at ``create_task`` time and wraps the child coroutine.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Coroutine, Optional, TypeVar

from opentelemetry import context as otel_context

T = TypeVar("T")

if sys.version_info >= (3, 11):

    class PropagatingTaskGroup(asyncio.TaskGroup):
        """An :class:`asyncio.TaskGroup` that preserves OTEL context.

        Usage::

            async with PropagatingTaskGroup() as tg:
                tg.create_task(some_coro())
        """

        def create_task(
            self,
            coro: Coroutine[Any, Any, T],
            *,
            name: Optional[str] = None,
            context: Optional[otel_context.Context] = None,
        ) -> asyncio.Task[T]:
            ctx = context or otel_context.get_current()

            async def _wrapper() -> T:
                token = otel_context.attach(ctx)
                try:
                    return await coro
                finally:
                    otel_context.detach(token)

            return super().create_task(_wrapper(), name=name)

    def patch_taskgroup() -> None:
        """Replace ``asyncio.TaskGroup`` with ``PropagatingTaskGroup``."""
        asyncio.TaskGroup = PropagatingTaskGroup  # type: ignore[misc]

else:

    class PropagatingTaskGroup:  # type: ignore[no-redef]
        """Placeholder — ``asyncio.TaskGroup`` requires Python 3.11+."""

        def __init__(self, *args: Any, **kwargs: Any):
            raise RuntimeError("TaskGroup requires Python 3.11+")

    def patch_taskgroup() -> None:
        """No-op on Python < 3.11."""
