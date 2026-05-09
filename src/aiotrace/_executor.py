"""Executor (thread-pool) context propagation for OpenTelemetry.

``run_in_executor`` runs the callable in a thread-pool thread, which
does **not** have access to the asyncio task's ``contextvars``.
OTEL context must be explicitly copied to the worker thread.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, TypeVar

from opentelemetry import context as otel_context

T = TypeVar("T")


def run_in_executor_with_context(
    executor: Optional[Any],
    func: Callable[..., T],
    *args: Any,
) -> asyncio.Future[T]:
    """Schedule ``func(*args, **kwargs)`` in an executor, preserving OTEL context.

    Usage::

        result = await run_in_executor_with_context(None, blocking_io, path)
    """
    ctx = otel_context.get_current()

    def wrapper() -> T:
        token = otel_context.attach(ctx)
        try:
            return func(*args)
        finally:
            otel_context.detach(token)

    loop = asyncio.get_running_loop()
    return loop.run_in_executor(executor, wrapper)


def wrap_run_in_executor(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Monkey-patch ``loop.run_in_executor`` to preserve OTEL context."""
    if loop is None:
        loop = asyncio.get_running_loop()
    original = loop.run_in_executor

    def _run_in_executor_with_context(
        executor: Optional[Any],
        func: Callable[..., T],
        *args: Any,
    ) -> asyncio.Future[T]:
        ctx = otel_context.get_current()

        def wrapper() -> T:
            token = otel_context.attach(ctx)
            try:
                return func(*args)
            finally:
                otel_context.detach(token)

        return original(executor, wrapper)

    loop.run_in_executor = _run_in_executor_with_context
