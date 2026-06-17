import os

import openapi_pydantic as openapi
import pytest
from fastmcp import Client
from mcp.types import ToolAnnotations
from pytest_mock import MockerFixture
from respx import MockRouter

from flagsmith_mcp import config, constants, server
from flagsmith_mcp.middleware import RootRouterMiddleware


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
    respx_mock: MockRouter,
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
    respx_mock.get(constants.OPENAPI_SPEC_URL).respond(
        json=spec.model_dump(by_alias=True, exclude_none=True, mode="json")
    )

    # When
    async with Client(transport=server.create_server(config.Settings())) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    # Then the tool is annotated according to the HTTP method's semantics
    assert tools["op"].annotations == expected


async def test_create_server__untagged_route__excluded_from_tools(
    respx_mock: MockRouter,
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
    respx_mock.get(constants.OPENAPI_SPEC_URL).respond(
        json=spec.model_dump(by_alias=True, exclude_none=True, mode="json")
    )

    # When
    async with Client(transport=server.create_server(config.Settings())) as client:
        names = {tool.name for tool in await client.list_tools()}

    # Then only the mcp-tagged route is exposed as a tool
    assert names == {"tagged"}


def test_run__configured_transport__runs_server_with_it(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(
        os.environ,
        {"TRANSPORT": "stdio", "FLAGSMITH_API_TOKEN": "ser.secret"},
        clear=True,
    )
    create_server_mock = mocker.patch.object(server, "create_server", autospec=True)
    setup_telemetry_mock = mocker.patch.object(server, "setup_telemetry", autospec=True)

    # When
    server.run()

    # Then
    setup_telemetry_mock.assert_called_once()
    create_server_mock.return_value.run.assert_called_once_with(
        transport="stdio", show_banner=False
    )


def test_run__metrics_port_unset__metrics_server_not_started(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.object(server, "create_server", autospec=True)
    mocker.patch.object(server, "setup_telemetry", autospec=True)
    start_http_server_mock = mocker.patch.object(
        server, "start_http_server", autospec=True
    )

    # When
    server.run()

    # Then
    start_http_server_mock.assert_not_called()


def test_run__metrics_port_set__metrics_server_started_with_it(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {"METRICS_PORT": "9464"}, clear=True)
    mocker.patch.object(server, "create_server", autospec=True)
    mocker.patch.object(server, "setup_telemetry", autospec=True)
    start_http_server_mock = mocker.patch.object(
        server, "start_http_server", autospec=True
    )

    # When
    server.run()

    # Then
    start_http_server_mock.assert_called_once_with(9464)


def test_run__http_transport__banner_off_uvicorn_logs_propagated(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(os.environ, {}, clear=True)
    create_server_mock = mocker.patch.object(server, "create_server", autospec=True)
    mocker.patch.object(server, "setup_telemetry", autospec=True)

    # When
    server.run()

    # Then the server is served on the streamable HTTP path, with logs
    # propagated and the root router installed
    _, kwargs = create_server_mock.return_value.run.call_args
    assert kwargs["transport"] == "http"
    assert kwargs["show_banner"] is False
    assert kwargs["path"] == constants.STREAMABLE_HTTP_PATH
    assert kwargs["uvicorn_config"] == {"log_config": None}
    (root_router,) = kwargs["middleware"]
    assert root_router.cls is RootRouterMiddleware
