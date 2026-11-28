from collections.abc import Generator

import pytest
from opentelemetry import baggage
from opentelemetry import context as otel_context


@pytest.fixture()
def mcp_baggage() -> Generator[None, None, None]:
    ctx = baggage.set_baggage("flagsmith.client.name", "flagsmith-mcp")
    token = otel_context.attach(ctx)
    yield
    otel_context.detach(token)
