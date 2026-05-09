"""pytest fixtures for aiotrace tests.

WARNING: ``set_tracer_provider`` uses an internal ``Once`` guard — calling
``get_tracer_provider()`` during import (e.g. via module-level code in any
test file) consumes it, making all subsequent ``set_tracer_provider()``
calls no-ops.  We work around this by directly assigning
``trace._TRACER_PROVIDER`` instead.
"""

from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, Span, SpanExporter


class CapturingExporter(SpanExporter):
    """Collects exported spans in memory for test assertions."""

    def __init__(self):
        self.spans: list[Span] = []

    def export(self, spans: list[Span]) -> None:
        self.spans.extend(spans)

    def shutdown(self) -> None:
        self.spans.clear()


@pytest.fixture
def exporter() -> CapturingExporter:
    return CapturingExporter()


@pytest.fixture(autouse=True)
def setup_otel(exporter: CapturingExporter):
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Direct assignment to bypass OTEL's Once guard
    trace._TRACER_PROVIDER = provider
    yield
    trace._TRACER_PROVIDER = None


@pytest.fixture
def tracer():
    return trace.get_tracer("aiotrace.test")
