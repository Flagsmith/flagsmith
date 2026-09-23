from collections.abc import Generator

import pytest
from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Span


@pytest.fixture()
def mcp_baggage() -> Generator[None, None, None]:
    ctx = baggage.set_baggage("flagsmith.client.name", "flagsmith-mcp")
    token = otel_context.attach(ctx)
    yield
    otel_context.detach(token)


@pytest.fixture()
def recording_span() -> Generator[Span, None, None]:
    tracer = TracerProvider().get_tracer("test")
    with tracer.start_as_current_span("test") as span:
        yield span
