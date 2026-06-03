from collections.abc import AsyncIterator
from typing import Callable

import httpx
import openapi_pydantic as openapi
import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import FastMCPTransport
from respx import MockRouter

from flagsmith_mcp import config, constants
from flagsmith_mcp import server as server_module

HTTPClientFactoryFixture = Callable[[FastMCP], AsyncIterator[httpx.AsyncClient]]


@pytest.fixture
def openapi_spec() -> openapi.OpenAPI:
    ok = openapi.Response(description="OK")
    return openapi.OpenAPI(
        info=openapi.Info(title="Flagsmith API", version="1.0.0"),
        paths={
            "/environments/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="list_environments", tags=["mcp"], responses={"200": ok}
                ),
            ),
            "/environments/{id}/": openapi.PathItem(
                delete=openapi.Operation(
                    operationId="delete_environment",
                    tags=["mcp"],
                    responses={"200": ok},
                ),
            ),
            "/internal/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="internal_only", responses={"200": ok}
                ),
            ),
        },
    )


@pytest.fixture(autouse=True)
def openapi_spec_mock(respx_mock: MockRouter, openapi_spec: openapi.OpenAPI) -> None:
    # create_server fetches the OpenAPI spec over HTTP; mock that call (respx
    # leaves the in-memory ASGI transport used by the tests untouched).
    respx_mock.get(constants.OPENAPI_SPEC_URL).respond(
        json=openapi_spec.model_dump(by_alias=True, exclude_none=True, mode="json")
    )


@pytest.fixture
def server() -> FastMCP:
    return server_module.create_server(config.Settings())


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client[FastMCPTransport]]:
    async with Client(transport=server) as connected:
        yield connected


@pytest.fixture
def http_client_factory() -> HTTPClientFactoryFixture:
    async def factory(server: FastMCP) -> AsyncIterator[httpx.AsyncClient]:
        transport = httpx.ASGITransport(app=server.http_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as connected:
            yield connected

    return factory


@pytest.fixture
async def http_client(
    server: FastMCP,
    http_client_factory: HTTPClientFactoryFixture,
) -> AsyncIterator[httpx.AsyncClient]:
    async for client in http_client_factory(server):
        yield client
