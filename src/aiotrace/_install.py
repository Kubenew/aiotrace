"""Central ``install()`` / ``uninstall()`` entry point.

Calling ``install()`` monkey-patches ``asyncio.create_task``,
``asyncio.Queue``, ``asyncio.Lock``, etc., with context-propagating
wrappers.  Use ``uninstall()`` to restore the originals.
"""

from __future__ import annotations

from aiotrace._lock import patch_locks
from aiotrace._queue import patch_queue
from aiotrace._task import unwrap_create_task, wrap_create_task
from aiotrace._taskgroup import patch_taskgroup

_installed = False


def install(*, queue: bool = True, locks: bool = True) -> None:
    """Monkey-patch asyncio primitives to propagate OTEL context.

    Patches applied:

    * ``asyncio.create_task`` — wraps child coroutines to restore
      the parent's OTEL context at creation time.
    * ``asyncio.Queue`` → :class:`aiotrace.PropagatingQueue` (opt-in).
    * ``asyncio.{Lock,Event,Semaphore,Condition}`` → propagating
      versions (opt-in).
    * ``asyncio.TaskGroup`` → :class:`aiotrace.PropagatingTaskGroup`
      (Python 3.11+).

    Args:
        queue: Whether to replace ``asyncio.Queue``.
        locks: Whether to replace lock primitives.
    """
    global _installed
    if _installed:
        return

    wrap_create_task()

    if queue:
        patch_queue()

    if locks:
        patch_locks()

    patch_taskgroup()

    _installed = True


def uninstall() -> None:
    """Restore all original asyncio primitives."""
    global _installed
    unwrap_create_task()
    _installed = False


def is_installed() -> bool:
    """Return ``True`` if ``install()`` has been called."""
    return _installed
