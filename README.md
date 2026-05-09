# aiotrace – Async context propagation for OpenTelemetry

[![PyPI](https://img.shields.io/pypi/v/aiotrace)](https://pypi.org/project/aiotrace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/aiotrace)](https://pypi.org/project/aiotrace/)
[![License](https://img.shields.io/pypi/l/aiotrace)](https://github.com/Kubenew/aiotrace/blob/main/LICENSE)
[![GitHub](https://img.shields.io/github/stars/Kubenew/aiotrace?style=social)](https://github.com/Kubenew/aiotrace)
[![Tests](https://img.shields.io/github/actions/workflow/status/Kubenew/aiotrace/ci.yml?label=tests)](https://github.com/Kubenew/aiotrace/actions)
[![Downloads](https://img.shields.io/pepy/dt/aiotrace)](https://pepy.tech/projects/aiotrace)

Fixes OpenTelemetry context propagation across asyncio boundaries:
`create_task`, `Queue`, `Lock`, `Event`, `Semaphore`, `TaskGroup`, and
`run_in_executor` (thread pool).

## Problem

OpenTelemetry stores the current span in a `contextvars.ContextVar`.
When asyncio tasks are created or resumed, Python copies/shallow-copies
these contextvars.  On Python < 3.9.17 / 3.10.7 / 3.11.1, `Task.__step`
does **not** restore the task's own context, causing:

* Spans created in child tasks appearing under the wrong parent
* Context leaking between producer/consumer queues
* Lost context when using `run_in_executor` (threads)

## Quick Start

```python
import asyncio
from opentelemetry import trace
from aiotrace import install

install()

tracer = trace.get_tracer(__name__)

async def child():
    with tracer.start_as_current_span("child"):
        pass

async def main():
    with tracer.start_as_current_span("parent"):
        await asyncio.create_task(child())

asyncio.run(main())
```

## Manual Usage (no monkey-patching)

```python
from aiotrace import create_task_with_context, PropagatingQueue

# Use explicit wrapper instead of monkey-patch
task = create_task_with_context(some_coro())

# Explicit propagating queue
queue = PropagatingQueue()
await queue.put(item)
item = await queue.get()
```

## Installation

```bash
pip install aiotrace
```

## What Gets Patched

| Primitive | Replacement | Description |
|-----------|-------------|-------------|
| `asyncio.create_task` | Wrapped | Captures OTEL context at task creation, restores inside child |
| `asyncio.Queue` | `PropagatingQueue` | Re-attaches context after `get()`/`put()` resume |
| `asyncio.Lock` | `PropagatingLock` | Re-attaches context after `acquire()` |
| `asyncio.Event` | `PropagatingEvent` | Re-attaches context after `wait()` |
| `asyncio.Semaphore` | `PropagatingSemaphore` | Re-attaches context after `acquire()` |
| `asyncio.Condition` | `PropagatingCondition` | Re-attaches context after `wait()` |
| `asyncio.TaskGroup` (3.11+) | `PropagatingTaskGroup` | Captures context at `create_task()` |

## API

### `install(patch_queue=True, patch_locks=True)`

Monkey-patches asyncio primitives. Safe to call multiple times (idempotent).

### `uninstall()`

Restores original asyncio primitives.

### `PropagatingQueue(maxsize=0)`

Drop-in replacement for `asyncio.Queue` with context propagation.

### `PropagatingLock`, `PropagatingEvent`, `PropagatingSemaphore`, `PropagatingCondition`

Drop-in replacements for synchronization primitives.

### `create_task_with_context(coro, *, name=None, otel_ctx=None)`

Create a task with explicit OTEL context propagation.

### `run_in_executor_with_context(executor, func, *args)`

Schedule a function in a thread pool with OTEL context.

## How It Works

`asyncio` creates new tasks by shallow-copying ``contextvars``, which can break OpenTelemetry's span hierarchy when tasks resume in the wrong context.  ``aiotrace`` fixes this at four levels:

1. **Wrapping ``create_task``** — Captures the current OTEL context before a task is spawned and restores it when the task's coroutine begins execution.

2. **Patching queues and locks** — For synchronization primitives, the context that a waiter had when it called ``get()`` or ``acquire()`` is stored and re-attached right before the waiter is resumed, using proper token-based attach/detach to prevent leaks.

3. **Propagating to threads** — ``run_in_executor_with_context`` copies the context to the worker thread via ``otel_context.attach()`` inside the thread's callable.

4. **TaskGroup support** (Python 3.11+) — Overrides ``create_task`` to ensure child tasks inherit the group's context.

All modifications are opt-in via ``install()`` or by using explicit classes like ``PropagatingQueue``.

## Limitations

- ``asyncio.Event`` and ``asyncio.Semaphore`` are patched but not yet verified for all edge cases (contributions welcome).
- Monkey-patching ``asyncio.Queue`` globally may conflict with other libraries that also replace it.  Use explicit ``PropagatingQueue`` when possible.
- High-frequency context switching adds a small overhead (approx. 1–2 µs per operation).  For most applications this is negligible.

## Requirements

* Python 3.8–3.12
* ``opentelemetry-api >= 1.20.0``

## License

MIT
