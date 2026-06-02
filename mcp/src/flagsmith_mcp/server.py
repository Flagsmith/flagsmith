from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, OpenAPITool, RouteMap
from fastmcp.utilities.components import FastMCPComponent
from fastmcp.utilities.openapi.models import HttpMethod, HTTPRoute
from mcp.types import ToolAnnotations

from flagsmith_mcp import config, constants
from flagsmith_mcp.auth import FlagsmithAuth

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
    return FastMCP.from_openapi(
        openapi_spec=_fetch_spec(),
        client=httpx.AsyncClient(
            base_url=settings.flagsmith_api_url,
            auth=FlagsmithAuth(settings.flagsmith_api_token),
        ),
        name="Flagsmith",
        route_maps=ROUTE_MAPS,
        mcp_component_fn=_customise,
    )


def run() -> None:
    settings = config.Settings()
    create_server(settings).run(transport=settings.transport)
