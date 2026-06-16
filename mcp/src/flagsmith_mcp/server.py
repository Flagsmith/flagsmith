from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, OpenAPITool, RouteMap
from fastmcp.utilities.components import FastMCPComponent
from fastmcp.utilities.openapi.models import HttpMethod, HTTPRoute
from mcp.types import ToolAnnotations
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_client import start_http_server
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from flagsmith_mcp import config, constants
from flagsmith_mcp.auth import FlagsmithAuth
from flagsmith_mcp.events import EventLoggingMiddleware
from flagsmith_mcp.metrics import PrometheusMiddleware
from flagsmith_mcp.middleware import RootRouterMiddleware
from flagsmith_mcp.oauth import FlagsmithResourceAuth
from flagsmith_mcp.telemetry import propagate_span_attributes, setup_telemetry

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
    api_client = httpx.AsyncClient(
        base_url=settings.flagsmith_api_url,
        auth=FlagsmithAuth(settings.flagsmith_api_token),
        event_hooks={"request": [propagate_span_attributes]},
    )
    # Instrument only the Flagsmith API client: emit a span per upstream
    # call and propagate W3C trace context; the event hook passes the MCP
    # call context to the API as W3C Baggage.
    HTTPXClientInstrumentor().instrument_client(api_client)
    server = FastMCP.from_openapi(
        openapi_spec=_fetch_spec(),
        client=api_client,
        name="Flagsmith",
        route_maps=ROUTE_MAPS,
        mcp_component_fn=_customise,
        validate_output=False,  # TODO https://github.com/Flagsmith/flagsmith/issues/7679
        auth=auth,
    )

    server.add_middleware(PrometheusMiddleware())
    server.add_middleware(EventLoggingMiddleware())

    @server.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    return server


def run() -> None:
    settings = config.Settings()
    setup_telemetry(settings)
    server = create_server(settings)
    if settings.metrics_port is not None:
        start_http_server(settings.metrics_port)
    if settings.transport == "http":
        server.run(
            transport=settings.transport,
            show_banner=False,
            path=constants.STREAMABLE_HTTP_PATH,
            middleware=[Middleware(RootRouterMiddleware)],
            # Let uvicorn log records propagate to the root logger so they
            # are rendered by the configured formatter.
            uvicorn_config={"log_config": None},
        )
    else:
        server.run(transport=settings.transport, show_banner=False)
