from drf_spectacular import generators
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularYAMLAPIView

from api.openapi import MCPSchemaGenerator, SchemaGenerator


class CustomSpectacularJSONAPIView(SpectacularJSONAPIView):  # type: ignore[misc]
    """
    JSON schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get_generator_class(self) -> type[generators.SchemaGenerator]:
        if self.request.query_params.get("mcp", "").lower() == "true":
            return MCPSchemaGenerator
        return SchemaGenerator


class CustomSpectacularYAMLAPIView(SpectacularYAMLAPIView):  # type: ignore[misc]
    """
    YAML schema view that supports ?mcp=true query parameter for MCP-filtered output.
    """

    def get_generator_class(self) -> type[generators.SchemaGenerator]:
        if self.request.query_params.get("mcp", "").lower() == "true":
            return MCPSchemaGenerator
        return SchemaGenerator
