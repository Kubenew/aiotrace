"""aiotrace — OpenTelemetry-native async context propagation for asyncio."""

from aiotrace._install import install, is_installed, uninstall
from aiotrace._lock import PropagatingLock
from aiotrace._queue import PropagatingQueue
from aiotrace._task import create_task_with_context, unwrap_create_task, wrap_create_task

__all__ = [
    "install",
    "uninstall",
    "is_installed",
    "wrap_create_task",
    "unwrap_create_task",
    "create_task_with_context",
    "PropagatingQueue",
    "PropagatingLock",
]

__version__ = "0.1.1"
