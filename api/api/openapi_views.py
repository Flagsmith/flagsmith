from typing import Any

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularYAMLAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.openapi import MCPSchemaGenerator, SchemaGenerator


class _MCPSchemaViewMixin:
    """
    Mixin that provides MCP schema generator selection based on ?mcp=true query parameter.
    """

    def get_generator_class(self) -> type:
        try:
            if self.request.query_params["mcp"].lower() == "true":  # type: ignore[attr-defined]
                return MCPSchemaGenerator
        except (AttributeError, KeyError):
            pass
        return SchemaGenerator

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.generator_class = self.get_generator_class()
        return super().get(request, *args, **kwargs)  # type: ignore[misc, no-any-return]


class CustomSpectacularJSONAPIView(_MCPSchemaViewMixin, SpectacularJSONAPIView):
    """
    JSON schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """


class CustomSpectacularYAMLAPIView(_MCPSchemaViewMixin, SpectacularYAMLAPIView):
    """
    YAML schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """
