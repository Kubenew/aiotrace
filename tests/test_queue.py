"""Tests for queue context propagation."""

from __future__ import annotations

import asyncio

import pytest

from aiotrace import PropagatingQueue


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
