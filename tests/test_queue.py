"""Tests for queue context propagation."""

from __future__ import annotations

import asyncio

import pytest

from aiotrace import PropagatingQueue, install


@pytest.mark.asyncio
async def test_queue_producer_consumer_spans(tracer, exporter):
    async def consumer(q: asyncio.Queue):
        item = await q.get()
        with tracer.start_as_current_span("process"):
            pass
        q.task_done()
        return item

    async def producer(q: asyncio.Queue):
        with tracer.start_as_current_span("produce"):
            await q.put("item")

    q = PropagatingQueue()
    prod = asyncio.create_task(producer(q))
    cons = asyncio.create_task(consumer(q))
    await asyncio.gather(prod, cons)
    await q.join()

    names = {s.name for s in exporter.spans}
    assert "produce" in names
    assert "process" in names


@pytest.mark.asyncio
async def test_queue_multiple_consumers(tracer, exporter):
    async def consumer(q: asyncio.Queue, name: str):
        await q.get()
        with tracer.start_as_current_span(f"consume_{name}"):
            pass
        q.task_done()

    async def producer(q: asyncio.Queue):
        with tracer.start_as_current_span("produce"):
            for i in range(3):
                await q.put(i)

    q = PropagatingQueue(maxsize=1)
    prod = asyncio.create_task(producer(q))
    cons = [asyncio.create_task(consumer(q, str(i))) for i in range(3)]
    await asyncio.gather(prod, *cons)
    await q.join()

    assert len(exporter.spans) >= 4


@pytest.mark.asyncio
async def test_queue_standard_behavior(tracer, exporter):
    q = PropagatingQueue()
    await q.put(1)
    await q.put(2)
    result = await q.get()
    assert result == 1
    result = await q.get()
    assert result == 2
    assert q.empty()


@pytest.mark.asyncio
async def test_queue_child_span_nests_under_producer(tracer, exporter):
    q = PropagatingQueue()

    async def consumer():
        item = await q.get()
        with tracer.start_as_current_span("consumer"):
            pass
        return item

    async def producer():
        with tracer.start_as_current_span("producer"):
            await q.put("x")
            await asyncio.create_task(consumer())

    await producer()

    spans = {s.name: s for s in exporter.spans}
    assert "producer" in spans
    assert "consumer" in spans


@pytest.mark.asyncio
async def test_install_patches_queue(tracer, exporter):
    install()

    q = asyncio.Queue()

    async def worker():
        with tracer.start_as_current_span("worker"):
            await q.get()

    with tracer.start_as_current_span("producer"):
        await q.put("data")
        await asyncio.create_task(worker())

    names = {s.name for s in exporter.spans}
    assert "producer" in names
    assert "worker" in names


@pytest.mark.asyncio
async def test_queue_cancellation_no_context_leak(tracer, exporter):
    q = PropagatingQueue()

    async def waiter():
        with tracer.start_as_current_span("waiter"):
            await q.get()

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    await q.put("cleanup")
    assert any(s.name == "waiter" for s in exporter.spans)
