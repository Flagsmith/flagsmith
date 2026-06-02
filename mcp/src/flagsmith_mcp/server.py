from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, OpenAPITool, RouteMap
from fastmcp.utilities.components import FastMCPComponent
from fastmcp.utilities.openapi.models import HttpMethod, HTTPRoute
from mcp.types import ToolAnnotations

from flagsmith_mcp import config, constants

ROUTE_MAPS = [
    RouteMap(tags={"mcp"}, mcp_type=MCPType.TOOL),
    RouteMap(mcp_type=MCPType.EXCLUDE),
]

# Annotation hints follow HTTP method semantics per RFC 9110.
READ_ONLY_METHODS: set[HttpMethod] = {"GET", "HEAD"}
DESTRUCTIVE_METHODS: set[HttpMethod] = {"DELETE"}
NON_IDEMPOTENT_METHODS: set[HttpMethod] = {"POST"}


def _annotate(method: HttpMethod) -> ToolAnnotations:
    read_only = method in READ_ONLY_METHODS
    return ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=method in DESTRUCTIVE_METHODS,
        idempotentHint=method not in NON_IDEMPOTENT_METHODS,
    )


def _customise(route: HTTPRoute, component: FastMCPComponent) -> None:
    if isinstance(component, OpenAPITool):
        component.annotations = _annotate(route.method)


def _fetch_spec() -> dict[str, Any]:
    response = httpx.get(constants.OPENAPI_SPEC_URL)
    response.raise_for_status()
    spec: dict[str, Any] = response.json()
    return spec


def create_server(settings: config.Settings) -> FastMCP[None]:
    return FastMCP.from_openapi(
        openapi_spec=_fetch_spec(),
        client=httpx.AsyncClient(base_url=settings.flagsmith_api_url),
        name="Flagsmith",
        route_maps=ROUTE_MAPS,
        mcp_component_fn=_customise,
    )


def run() -> None:
    settings = config.Settings()
    create_server(settings).run(transport=settings.transport)
