from typing import Any

import openapi_pydantic as openapi
import pytest
from fastmcp import Client
from mcp.types import ToolAnnotations
from pytest_httpx import HTTPXMock

from flagsmith_mcp import config, constants, server


@pytest.mark.parametrize(
    "method, expected",
    [
        (
            "get",
            ToolAnnotations(
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
            ),
        ),
        (
            "head",
            ToolAnnotations(
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
            ),
        ),
        (
            "delete",
            ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=True,
                idempotentHint=True,
            ),
        ),
        (
            "put",
            ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
            ),
        ),
        (
            "patch",
            ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
            ),
        ),
        (
            "post",
            ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
            ),
        ),
    ],
)
async def test_create_server__mcp_route__annotates_tool_per_method(
    httpx_mock: HTTPXMock,
    method: str,
    expected: ToolAnnotations,
) -> None:
    # Given a spec with a single mcp-tagged route using the parametrised method
    operation = openapi.Operation(
        operationId="op",
        tags=["mcp"],
        responses={"200": openapi.Response(description="OK")},
    )
    spec = openapi.OpenAPI(
        info=openapi.Info(title="Flagsmith API", version="1.0.0"),
        paths={"/things/": openapi.PathItem.model_validate({method: operation})},
    )
    httpx_mock.add_response(
        url=constants.OPENAPI_SPEC_URL,
        json=spec.model_dump(by_alias=True, exclude_none=True, mode="json"),
    )

    # When
    async with Client(transport=server.create_server(config.Settings())) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    # Then the tool is annotated according to the HTTP method's semantics
    assert tools["op"].annotations == expected


async def test_create_server__untagged_route__excluded_from_tools(
    httpx_mock: HTTPXMock,
) -> None:
    # Given a spec with one mcp-tagged route and one untagged route
    spec = openapi.OpenAPI(
        info=openapi.Info(title="Flagsmith API", version="1.0.0"),
        paths={
            "/tagged/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="tagged",
                    tags=["mcp"],
                    responses={"200": openapi.Response(description="OK")},
                )
            ),
            "/untagged/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="untagged",
                    responses={"200": openapi.Response(description="OK")},
                )
            ),
        },
    )
    httpx_mock.add_response(
        url=constants.OPENAPI_SPEC_URL,
        json=spec.model_dump(by_alias=True, exclude_none=True, mode="json"),
    )

    # When
    async with Client(transport=server.create_server(config.Settings())) as client:
        names = {tool.name for tool in await client.list_tools()}

    # Then only the mcp-tagged route is exposed as a tool
    assert names == {"tagged"}


def test_run__configured_transport__runs_server_with_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    calls: dict[str, Any] = {}

    class FakeServer:
        def run(self, transport: str) -> None:
            calls["transport"] = transport

    monkeypatch.setattr(server, "create_server", lambda settings: FakeServer())
    monkeypatch.setenv("TRANSPORT", "stdio")
    monkeypatch.setenv("FLAGSMITH_API_TOKEN", "ser.secret")

    # When
    server.run()

    # Then
    assert calls == {"transport": "stdio"}
