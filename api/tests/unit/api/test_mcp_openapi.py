from typing import Any
from unittest.mock import MagicMock

from api.openapi import MCPSchemaGenerator, SchemaGenerator
from api.openapi_views import CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView


def test_mcp_filter_paths__includes_operations_with_mcp_tag() -> None:
    # Given
    paths: dict[str, Any] = {
        "/api/v1/organisations/": {
            "get": {
                "operationId": "organisations_list",
                "tags": ["mcp", "organisations"],
                "description": "List organisations",
            },
        },
    }
    generator = MCPSchemaGenerator()

    # When
    filtered = generator._filter_paths(paths)

    # Then
    assert "/api/v1/organisations/" in filtered
    assert "get" in filtered["/api/v1/organisations/"]


def test_mcp_filter_paths__excludes_operations_without_mcp_tag() -> None:
    # Given
    paths: dict[str, Any] = {
        "/api/v1/users/": {
            "get": {
                "operationId": "users_list",
                "tags": ["users"],
                "description": "List users",
            },
        },
    }
    generator = MCPSchemaGenerator()

    # When
    filtered = generator._filter_paths(paths)

    # Then
    assert "/api/v1/users/" not in filtered


def test_mcp_filter_paths__mixed_operations() -> None:
    # Given
    paths: dict[str, Any] = {
        "/api/v1/organisations/": {
            "get": {
                "operationId": "organisations_list",
                "tags": ["mcp", "organisations"],
            },
            "post": {
                "operationId": "organisations_create",
                "tags": ["organisations"],  # No mcp tag
            },
        },
    }
    generator = MCPSchemaGenerator()

    # When
    filtered = generator._filter_paths(paths)

    # Then
    assert "/api/v1/organisations/" in filtered
    assert "get" in filtered["/api/v1/organisations/"]
    assert "post" not in filtered["/api/v1/organisations/"]


def test_mcp_transform_for_mcp__overrides_operation_id_with_x_mcp_name() -> None:
    # Given
    operation: dict[str, Any] = {
        "operationId": "organisations_list",
        "tags": ["mcp"],
        "x-mcp-name": "list_organisations",
    }
    generator = MCPSchemaGenerator()

    # When
    transformed = generator._transform_for_mcp(operation)

    # Then
    assert transformed["operationId"] == "list_organisations"
    assert "x-mcp-name" not in transformed


def test_mcp_transform_for_mcp__overrides_description_with_x_mcp_description() -> None:
    # Given
    operation: dict[str, Any] = {
        "operationId": "organisations_list",
        "tags": ["mcp"],
        "description": "Original description",
        "x-mcp-description": "MCP-specific description",
    }
    generator = MCPSchemaGenerator()

    # When
    transformed = generator._transform_for_mcp(operation)

    # Then
    assert transformed["description"] == "MCP-specific description"
    assert "x-mcp-description" not in transformed


def test_mcp_transform_for_mcp__preserves_original_when_no_extensions() -> None:
    # Given
    operation: dict[str, Any] = {
        "operationId": "organisations_list",
        "tags": ["mcp"],
        "description": "Original description",
    }
    generator = MCPSchemaGenerator()

    # When
    transformed = generator._transform_for_mcp(operation)

    # Then
    assert transformed["operationId"] == "organisations_list"
    assert transformed["description"] == "Original description"


def test_mcp_update_security_for_mcp__sets_api_key_security_scheme() -> None:
    # Given
    schema: dict[str, Any] = {
        "components": {
            "securitySchemes": {
                "Private": {"type": "apiKey"},
            },
        },
        "security": [{"Private": []}],
    }
    generator = MCPSchemaGenerator()

    # When
    updated = generator._update_security_for_mcp(schema)

    # Then
    assert "ApiKey" in updated["components"]["securitySchemes"]
    assert updated["security"] == [{"ApiKey": []}]
    # Original scheme should be replaced
    assert "Private" not in updated["components"]["securitySchemes"]


def test_mcp_get_schema__filters_and_transforms() -> None:
    # Given
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    # Schema should have standard OpenAPI structure
    assert "$schema" in schema
    assert "paths" in schema
    assert "components" in schema
    # Security should be MCP-specific
    assert "ApiKey" in schema["components"]["securitySchemes"]


def test_custom_json_view__returns_mcp_generator_when_mcp_param_is_true() -> None:
    # Given
    view = CustomSpectacularJSONAPIView()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "true"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is MCPSchemaGenerator


def test_custom_json_view__returns_schema_generator_when_mcp_param_is_false() -> None:
    # Given
    view = CustomSpectacularJSONAPIView()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "false"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is SchemaGenerator


def test_custom_json_view__returns_schema_generator_when_no_mcp_param() -> None:
    # Given
    view = CustomSpectacularJSONAPIView()
    view.request = MagicMock()
    view.request.query_params = {}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is SchemaGenerator


def test_custom_yaml_view__returns_mcp_generator_when_mcp_param_is_true() -> None:
    # Given
    view = CustomSpectacularYAMLAPIView()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "true"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is MCPSchemaGenerator


def test_custom_yaml_view__returns_schema_generator_when_no_mcp_param() -> None:
    # Given
    view = CustomSpectacularYAMLAPIView()
    view.request = MagicMock()
    view.request.query_params = {}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is SchemaGenerator


def test_custom_json_view__case_insensitive_mcp_param() -> None:
    # Given
    view = CustomSpectacularJSONAPIView()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "TRUE"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is MCPSchemaGenerator


def test_mcp_schema__includes_organisations_endpoint() -> None:
    # Given
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    assert "/api/v1/organisations/" in schema["paths"]
    org_list = schema["paths"]["/api/v1/organisations/"]["get"]
    assert org_list["operationId"] == "list_organisations"
    assert org_list["description"] == "Retrieve all organisations the user has access to."


def test_mcp_schema__includes_projects_endpoint() -> None:
    # Given
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    assert "/api/v1/projects/" in schema["paths"]
    project_list = schema["paths"]["/api/v1/projects/"]["get"]
    assert project_list["operationId"] == "list_projects"
    assert project_list["description"] == "Retrieve all projects the user has access to."


def test_mcp_schema__excludes_non_mcp_endpoints() -> None:
    # Given
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    # Users endpoint should not be in MCP schema (not tagged)
    assert "/api/v1/users/" not in schema["paths"]
