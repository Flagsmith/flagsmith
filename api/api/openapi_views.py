from typing import Any

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularYAMLAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.openapi import MCPSchemaGenerator, SchemaGenerator


class CustomSpectacularJSONAPIView(SpectacularJSONAPIView):  # type: ignore[misc]
    """
    JSON schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.query_params.get("mcp", "").lower() == "true":
            self.generator_class = MCPSchemaGenerator
        else:
            self.generator_class = SchemaGenerator
        return super().get(request, *args, **kwargs)


class CustomSpectacularYAMLAPIView(SpectacularYAMLAPIView):  # type: ignore[misc]
    """
    YAML schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.query_params.get("mcp", "").lower() == "true":
            self.generator_class = MCPSchemaGenerator
            response = super().get(request, *args, **kwargs)
            response["Content-Disposition"] = 'attachment; filename="mcp_openapi.yaml"'
            return response
        else:
            self.generator_class = SchemaGenerator
            return super().get(request, *args, **kwargs)
