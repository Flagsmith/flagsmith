from typing import TYPE_CHECKING, Any, Literal

from drf_spectacular import generators, openapi
from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension,
    OpenApiSerializerExtension,
)
from drf_spectacular.plumbing import ResolvedComponent, safe_ref
from drf_spectacular.plumbing import append_meta as append_meta_orig
from pydantic import TypeAdapter
from rest_framework.request import Request
from typing_extensions import is_typeddict


def append_meta(schema: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    """
    See https://github.com/tfranzel/drf-spectacular/issues/1480
    """
    try:
        return append_meta_orig(schema, meta)
    except AssertionError as exc:
        if str(exc) == "Invalid nullable case":
            pass
        else:  # pragma: no cover
            raise exc

    if any("nullable" in d for d in (schema, meta)) and "oneOf" in schema:
        schema = schema.copy()
        meta = meta.copy()

        schema.pop("nullable", None)
        meta.pop("nullable", None)

        schema["oneOf"].append({"type": "null"})

    if "exclusiveMinimum" in schema and "minimum" in schema:  # pragma: no cover
        schema["exclusiveMinimum"] = schema.pop("minimum")
    if "exclusiveMaximum" in schema and "maximum" in schema:  # pragma: no cover
        schema["exclusiveMaximum"] = schema.pop("maximum")

    return safe_ref({**schema, **meta})


openapi.append_meta = append_meta  # type: ignore[attr-defined]


class SchemaGenerator(generators.SchemaGenerator):
    """
    Adds a `$schema` property to the root schema object.
    """

    if TYPE_CHECKING:
        # Parent class has no type_hints, this is used to ignore the type error upstream
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)  # type: ignore[no-untyped-call]

    def get_schema(
        self, request: Request | None = None, public: bool = False
    ) -> dict[str, Any]:
        schema: dict[str, Any] = super().get_schema(request, public)  # type: ignore[no-untyped-call]
        return {
            "$schema": "https://spec.openapis.org/oas/3.1/dialect/base",
            **schema,
        }


class MCPSchemaGenerator(SchemaGenerator):
    """
    Schema generator that filters to only include operations tagged with "mcp".

    Uses x-gram extension for Gram-native tool naming and descriptions.
    Gram reads x-gram directly from the spec.
    """

    MCP_TAG = "mcp"
    MCP_SERVER_URL = "https://api.flagsmith.com"

    def get_schema(
        self, request: Request | None = None, public: bool = False
    ) -> dict[str, Any]:
        schema = super().get_schema(request, public)
        schema["paths"] = self._filter_paths(schema.get("paths", {}))
        schema = self._update_security_for_mcp(schema)
        schema.pop("$schema", None)
        info = schema.pop("info").copy()
        info["title"] = "mcp_openapi"
        return {
            "openapi": schema.pop("openapi"),
            "info": info,
            "servers": [{"url": self.MCP_SERVER_URL}],
            **schema,
        }

    def _filter_paths(self, paths: dict[str, Any]) -> dict[str, Any]:
        """Filter paths to only include operations tagged with 'mcp'."""
        filtered_paths: dict[str, Any] = {}

        for path, path_item in paths.items():
            filtered_operations: dict[str, Any] = {}
            has_any_mcp_tag = False

            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    filtered_operations[method] = operation
                    continue

                tags = operation.get("tags", [])
                if self.MCP_TAG in tags:
                    filtered_operations[method] = self._transform_for_mcp(operation)
                    has_any_mcp_tag = True

            if has_any_mcp_tag:
                filtered_paths[path] = filtered_operations

        return filtered_paths

    def _transform_for_mcp(self, operation: dict[str, Any]) -> dict[str, Any]:
        """Apply MCP-specific transformations to an operation."""
        operation = operation.copy()
        # Remove operation-level security (use global MCP security instead)
        operation.pop("security", None)
        return operation

    def _update_security_for_mcp(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Update security schemes for MCP (Organisation API Key)."""
        schema = schema.copy()
        schema["components"] = schema.get("components", {}).copy()
        schema["components"]["securitySchemes"] = {
            "TOKEN_AUTH": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Organisation API Key. Format: Api-Key <key>",
            },
        }
        schema["security"] = [{"TOKEN_AUTH": []}]
        return schema


class TypedDictSchemaExtension(
    OpenApiSerializerExtension  # type: ignore[no-untyped-call]
):
    """
    An OpenAPI extension that allows drf-spectacular to generate schema documentation
    from TypedDicts via Pydantic.

    This extension is automatically used when a TypedDict subclass is passed
    as a response type in @extend_schema decorators.
    """

    @classmethod
    def _matches(cls, target: type[Any]) -> bool:
        return is_typeddict(target)

    def get_name(
        self,
        auto_schema: openapi.AutoSchema | None = None,
        direction: Literal["request", "response"] | None = None,
    ) -> str | None:
        return self.target.__name__  # type: ignore[no-any-return]

    def map_serializer(
        self,
        auto_schema: openapi.AutoSchema,
        direction: str,
    ) -> dict[str, Any]:
        model_json_schema = TypeAdapter(self.target).json_schema(
            mode="serialization",
            ref_template="#/components/schemas/%s{model}" % self.get_name(),
        )

        # Register nested definitions as components
        if "$defs" in model_json_schema:
            for ref_name, schema_kwargs in model_json_schema.pop("$defs").items():
                component = ResolvedComponent(  # type: ignore[no-untyped-call]
                    name=self.get_name() + ref_name,
                    type=ResolvedComponent.SCHEMA,
                    object=ref_name,
                    schema=schema_kwargs,
                )
                auto_schema.registry.register_on_missing(component)

        return model_json_schema


class EnvironmentKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "environments.authentication.EnvironmentKeyAuthentication"
    name = "Environment API Key"

    def get_security_definition(
        self, auto_schema: openapi.AutoSchema | None = None
    ) -> dict[str, Any]:
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-Environment-Key",
            "description": "For SDK endpoints. <a href='https://docs.flagsmith.com/clients/rest#public-api-endpoints'>Find out more</a>.",
        }


class MasterAPIKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "api_keys.authentication.MasterAPIKeyAuthentication"
    name = "Master API Key"

    def get_security_definition(
        self, auto_schema: openapi.AutoSchema | None = None
    ) -> dict[str, Any]:
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": (
                "<a href='https://docs.flagsmith.com/clients/rest#private-api-endpoints'>Find out more</a>."
            ),
        }
