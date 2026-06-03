from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, OpenAPITool, RouteMap
from fastmcp.utilities.components import FastMCPComponent
from fastmcp.utilities.openapi.models import HttpMethod, HTTPRoute
from mcp.types import ToolAnnotations
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from flagsmith_mcp import config, constants
from flagsmith_mcp.auth import FlagsmithAuth
from flagsmith_mcp.metrics import PrometheusMiddleware
from flagsmith_mcp.oauth import FlagsmithResourceAuth

ROUTE_MAPS = [
    RouteMap(tags={"mcp"}, mcp_type=MCPType.TOOL),
    RouteMap(mcp_type=MCPType.EXCLUDE),
]

# Annotation hints follow HTTP method semantics per RFC 9110.
READ_ONLY_METHODS: set[HttpMethod] = {"GET", "HEAD"}
DESTRUCTIVE_METHODS: set[HttpMethod] = {"DELETE"}
NON_IDEMPOTENT_METHODS: set[HttpMethod] = {"POST"}


def _customise(route: HTTPRoute, component: FastMCPComponent) -> None:
    # Our ROUTE_MAPS only ever yields tools
    assert isinstance(component, OpenAPITool)
    method = route.method
    component.annotations = ToolAnnotations(
        readOnlyHint=method in READ_ONLY_METHODS,
        destructiveHint=method in DESTRUCTIVE_METHODS,
        idempotentHint=method not in NON_IDEMPOTENT_METHODS,
    )


def _fetch_spec() -> dict[str, Any]:
    response = httpx.get(constants.OPENAPI_SPEC_URL)
    response.raise_for_status()
    spec: dict[str, Any] = response.json()
    return spec


def create_server(settings: config.Settings) -> FastMCP[None]:
    # OAuth discovery is the credential fallback for HTTP transport: only when
    # the server holds no static token does it advertise the AS and gate on a
    # missing Authorization header. Otherwise (stdio, static token, or a
    # forwarded --header) it's pure pass-through.
    auth = None
    if settings.transport == "http" and settings.flagsmith_api_token is None:
        auth = FlagsmithResourceAuth(
            resource_url=settings.mcp_server_url,
            authorization_server=settings.flagsmith_api_url,
        )
    server = FastMCP.from_openapi(
        openapi_spec=_fetch_spec(),
        client=httpx.AsyncClient(
            base_url=settings.flagsmith_api_url,
            auth=FlagsmithAuth(settings.flagsmith_api_token),
        ),
        name="Flagsmith",
        route_maps=ROUTE_MAPS,
        mcp_component_fn=_customise,
        validate_output=False,  # TODO https://github.com/Flagsmith/flagsmith/issues/7679
        auth=auth,
    )

    server.add_middleware(PrometheusMiddleware())

    @server.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    @server.custom_route("/metrics", methods=["GET"])
    async def metrics(request: Request) -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return server


def run() -> None:
    settings = config.Settings()
    create_server(settings).run(transport=settings.transport)
