import types
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from flagsmith_mcp import config, server


@pytest.mark.parametrize(
    "method, read_only, destructive, idempotent",
    [
        ("GET", True, False, True),
        ("HEAD", True, False, True),
        ("DELETE", False, True, True),
        ("PUT", False, False, True),
        ("PATCH", False, False, True),
        ("POST", False, False, False),
    ],
)
def test_annotate__http_method__maps_hints(
    method: str,
    read_only: bool,
    destructive: bool,
    idempotent: bool,
) -> None:
    # When
    annotations = server._annotate(method)  # type: ignore[arg-type]

    # Then
    assert annotations.readOnlyHint is read_only
    assert annotations.destructiveHint is destructive
    assert annotations.idempotentHint is idempotent


def test_fetch_spec__spec_endpoint__returns_schema(httpx_mock: HTTPXMock) -> None:
    # Given
    schema = {"openapi": "3.1.0", "info": {"title": "Flagsmith API", "version": "1"}}
    httpx_mock.add_response(url=config.OPENAPI_SPEC_URL, json=schema)

    # When
    spec = server._fetch_spec()

    # Then
    assert spec == schema


def test_customise__non_tool_component__leaves_annotations_untouched() -> None:
    # Given
    component = types.SimpleNamespace(annotations=None)

    # When
    server._customise(route=None, component=component)  # type: ignore[arg-type]

    # Then
    assert component.annotations is None


def test_run__configured_transport__runs_server_with_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    calls: dict[str, Any] = {}

    class FakeServer:
        def run(self, transport: str) -> None:
            calls["transport"] = transport

    monkeypatch.setattr(server, "create_server", lambda: FakeServer())
    monkeypatch.setattr(config, "get_transport", lambda: "stdio")

    # When
    server.run()

    # Then
    assert calls == {"transport": "stdio"}
