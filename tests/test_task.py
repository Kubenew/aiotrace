"""Tests for task context propagation."""

from __future__ import annotations

import asyncio
import sys

import pytest

from aiotrace import unwrap_create_task, wrap_create_task


@pytest.mark.asyncio
async def test_child_task_inherits_parent_context(tracer, exporter):
    wrap_create_task()
    try:
        async def child():
            with tracer.start_as_current_span("child"):
                pass

        async def parent():
            with tracer.start_as_current_span("parent"):
                await asyncio.create_task(child())

        await parent()
        assert len(exporter.spans) == 2
        names = {s.name for s in exporter.spans}
        assert names == {"parent", "child"}
    finally:
        unwrap_create_task()


@pytest.mark.asyncio
async def test_gather_preserves_context(tracer, exporter):
    wrap_create_task()
    try:
        async def child(n):
            with tracer.start_as_current_span(f"child_{n}"):
                pass

        async def parent():
            with tracer.start_as_current_span("parent"):
                await asyncio.gather(child(1), child(2), child(3))

        await parent()
        assert len(exporter.spans) == 4
    finally:
        unwrap_create_task()


@pytest.mark.asyncio
async def test_nested_create_task(tracer, exporter):
    wrap_create_task()
    try:
        async def inner():
            with tracer.start_as_current_span("inner"):
                pass

        async def outer():
            with tracer.start_as_current_span("outer"):
                await asyncio.create_task(inner())

        await outer()
        assert len(exporter.spans) == 2
        names = {s.name for s in exporter.spans}
        assert names == {"outer", "inner"}
    finally:
        unwrap_create_task()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="TaskGroup requires 3.11+")
@pytest.mark.asyncio
async def test_create_task_in_taskgroup(tracer, exporter):
    wrap_create_task()
    try:
        async def child():
            with tracer.start_as_current_span("child"):
                pass

        async def parent():
            with tracer.start_as_current_span("parent"):
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(child())
                    tg.create_task(child())

        await parent()
        assert len(exporter.spans) == 3
    finally:
        unwrap_create_task()


@pytest.mark.asyncio
async def test_context_maintained_after_task_cancel(tracer, exporter):
    wrap_create_task()
    try:
        async def cancellable():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise

        async def parent():
            with tracer.start_as_current_span("parent"):
                task = asyncio.create_task(cancellable())
                await asyncio.sleep(0.01)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await parent()
        assert len(exporter.spans) == 1
        assert exporter.spans[0].name == "parent"
    finally:
        unwrap_create_task()


@pytest.mark.asyncio
async def test_create_task_without_patch(tracer, exporter):
    """Sanity check: standard create_task on modern Python."""
    async def child():
        with tracer.start_as_current_span("child"):
            pass

    async def parent():
        with tracer.start_as_current_span("parent"):
            await asyncio.create_task(child())

    await parent()
    assert len(exporter.spans) == 2
