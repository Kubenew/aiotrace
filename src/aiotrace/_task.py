"""Task context propagation for OpenTelemetry.

Captures the OTEL context at task-creation time and restores it
inside the child task so that spans created in the child correctly
nest under the parent span.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar

from opentelemetry import context as otel_context

T = TypeVar("T")

_original_create_task: Optional[Callable[..., asyncio.Task]] = None


def create_task_with_context(
    coro: Coroutine[Any, Any, T],
    *,
    name: Optional[str] = None,
    otel_ctx: Optional[otel_context.Context] = None,
) -> asyncio.Task[T]:
    """Create an asyncio Task that preserves the current OTEL context.

    Unlike ``asyncio.create_task``, which relies on ``contextvars.copy_context()``
    at ``Task.__init__`` time, this wrapper explicitly captures the **OTEL**
    context and restores it inside the coroutine wrapper.  This guarantees
    that the child task sees the same OTEL context even if the parent's
    context changes between creation and first ``await``.

    Args:
        coro: The coroutine to run in the new task.
        name: Optional task name (passed through to ``asyncio.create_task``).
        otel_ctx: An explicit OTEL context to use.  Defaults to
            ``otel_context.get_current()`` at call time.

    Returns:
        A new ``asyncio.Task`` instance.
    """
    ctx = otel_ctx if otel_ctx is not None else otel_context.get_current()

    async def _wrapper() -> T:
        token = otel_context.attach(ctx)
        try:
            return await coro
        finally:
            otel_context.detach(token)

    return asyncio.create_task(_wrapper(), name=name)


def wrap_create_task() -> None:
    """Replace ``asyncio.create_task`` with a context-propagating version.

    This is a lighter alternative to ``install()`` – it only patches
    the task-creation boundary, not queues or locks.
    """
    global _original_create_task
    if _original_create_task is not None:
        return  # already wrapped

    _original_create_task = asyncio.create_task

    @wraps(_original_create_task)
    def _create_task_with_context(
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

        return _original_create_task(_wrapper(), name=name)

    asyncio.create_task = _create_task_with_context


def unwrap_create_task() -> None:
    """Restore the original ``asyncio.create_task``."""
    global _original_create_task
    if _original_create_task is not None:
        asyncio.create_task = _original_create_task
        _original_create_task = None


def _patch_loop_create_task(loop: asyncio.AbstractEventLoop) -> None:
    """Patch ``loop.create_task`` for the given event loop.

    Some libraries call ``loop.create_task`` directly instead of
    ``asyncio.create_task``.  This function patches the loop-level
    method for completeness.
    """
    original = loop.create_task

    @wraps(original)
    def _loop_create_task(
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

        return original(_wrapper(), name=name)

    loop.create_task = _loop_create_task
