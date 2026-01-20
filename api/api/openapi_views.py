from typing import Any

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularYAMLAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.openapi import MCPSchemaGenerator, SchemaGenerator


class CustomSpectacularJSONAPIView(SpectacularJSONAPIView):
    """
    JSON schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get_generator_class(self) -> type:
        if (
            getattr(self, "request", None)
            and self.request.query_params.get("mcp", "").lower() == "true"
        ):
            return MCPSchemaGenerator
        return SchemaGenerator

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.generator_class = self.get_generator_class()
        return super().get(request, *args, **kwargs)  # type: ignore[no-untyped-call, no-any-return]


class CustomSpectacularYAMLAPIView(SpectacularYAMLAPIView):
    """
    YAML schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get_generator_class(self) -> type:
        if (
            getattr(self, "request", None)
            and self.request.query_params.get("mcp", "").lower() == "true"
        ):
            return MCPSchemaGenerator
        return SchemaGenerator

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.generator_class = self.get_generator_class()
        return super().get(request, *args, **kwargs)  # type: ignore[no-untyped-call, no-any-return]
