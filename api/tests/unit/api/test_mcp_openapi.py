from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_django.fixtures import SettingsWrapper

from api.openapi import MCPSchemaGenerator, SchemaGenerator
from api.openapi_views import CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView
from oauth2_metadata.dataclasses import OAuthConfig


def test_mcp_filter_paths__mcp_tagged_operation__includes_path() -> None:
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


def test_mcp_filter_paths__no_mcp_tag__excludes_path() -> None:
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


def test_mcp_filter_paths__mixed_mcp_and_non_mcp_operations__includes_only_mcp() -> (
    None
):
    # Given
    paths: dict[str, Any] = {
        "/api/v1/organisations/{id}/": {
            "parameters": [
                {"name": "id", "in": "path", "required": True},
            ],
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
    assert "/api/v1/organisations/{id}/" in filtered
    path_item = filtered["/api/v1/organisations/{id}/"]
    assert "get" in path_item
    assert "post" not in path_item
    assert path_item["parameters"] == [
        {"name": "id", "in": "path", "required": True},
    ]


def test_mcp_transform_for_mcp__x_gram_extension_present__preserves_extension() -> None:
    # Given
    operation: dict[str, Any] = {
        "operationId": "organisations_list",
        "tags": ["mcp"],
        "description": "Original description",
        "x-gram": {
            "name": "list_organisations",
            "description": "Gram-specific description",
        },
    }
    generator = MCPSchemaGenerator()

    # When
    transformed = generator._transform_for_mcp(operation)

    # Then
    assert transformed["x-gram"] == {
        "name": "list_organisations",
        "description": "Gram-specific description",
    }
    assert transformed["operationId"] == "organisations_list"
    assert transformed["description"] == "Original description"


def test_mcp_transform_for_mcp__no_extensions__preserves_original() -> None:
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


def test_mcp_transform_for_mcp__security_present__removes_operation_level_security() -> (
    None
):
    # Given
    operation: dict[str, Any] = {
        "operationId": "organisations_list",
        "tags": ["mcp"],
        "description": "Original description",
        "security": [{"Private": []}],
    }
    generator = MCPSchemaGenerator()

    # When
    transformed = generator._transform_for_mcp(operation)

    # Then
    assert "security" not in transformed


def test_mcp_update_security_for_mcp__existing_scheme__sets_oauth_and_token_auth() -> (
    None
):
    # Given
    oauth = OAuthConfig(
        api_url="https://api.flagsmith.example.com",
        frontend_url="https://app.flagsmith.example.com",
        scopes={"mcp": "MCP access"},
    )
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
    updated = generator._update_security_for_mcp(schema, oauth)

    # Then
    assert "Private" not in updated["components"]["securitySchemes"]
    assert "TOKEN_AUTH" in updated["components"]["securitySchemes"]
    oauth2_scheme = updated["components"]["securitySchemes"]["oauth2"]
    assert oauth2_scheme["type"] == "oauth2"
    auth_code_flow = oauth2_scheme["flows"]["authorizationCode"]
    assert (
        auth_code_flow["authorizationUrl"]
        == "https://app.flagsmith.example.com/oauth/authorize/"
    )
    assert auth_code_flow["tokenUrl"] == "https://api.flagsmith.example.com/o/token/"
    assert auth_code_flow["scopes"] == {"mcp": "MCP access"}
    assert updated["security"] == [{"oauth2": ["mcp"]}, {"TOKEN_AUTH": []}]


@pytest.mark.parametrize(
    "view_class",
    [CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView],
)
def test_custom_view__mcp_param_is_true__returns_mcp_generator(
    view_class: type,
) -> None:
    # Given
    view = view_class()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "true"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is MCPSchemaGenerator


@pytest.mark.parametrize(
    "view_class",
    [CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView],
)
def test_custom_view__mcp_param_is_false__returns_schema_generator(
    view_class: type,
) -> None:
    # Given
    view = view_class()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "false"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is SchemaGenerator


@pytest.mark.parametrize(
    "view_class",
    [CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView],
)
def test_custom_view__no_mcp_param__returns_schema_generator(
    view_class: type,
) -> None:
    # Given
    view = view_class()
    view.request = MagicMock()
    view.request.query_params = {}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is SchemaGenerator


@pytest.mark.parametrize(
    "view_class",
    [CustomSpectacularJSONAPIView, CustomSpectacularYAMLAPIView],
)
def test_custom_view__uppercase_mcp_param__returns_mcp_generator(
    view_class: type,
) -> None:
    # Given
    view = view_class()
    view.request = MagicMock()
    view.request.query_params = {"mcp": "TRUE"}

    # When
    generator_class = view.get_generator_class()

    # Then
    assert generator_class is MCPSchemaGenerator


def test_mcp_schema__full_schema_generated__includes_expected_endpoints_only() -> None:
    # Given
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    paths = schema["paths"]

    assert "/api/v1/organisations/" in paths
    assert paths["/api/v1/organisations/"]["get"]["x-gram"] == {
        "name": "list_organizations",
        "description": "Lists all organizations accessible with the provided user API key.",
    }

    assert "/api/v1/organisations/{id}/projects/" in paths
    assert paths["/api/v1/organisations/{id}/projects/"]["get"]["x-gram"] == {
        "name": "list_projects_in_organization",
        "description": "Retrieves all projects within a specified organization.",
    }

    assert "/api/v1/users/" not in paths


def test_mcp_schema__full_schema_generated__includes_server_from_settings(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://flagsmith.example.com/"
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    assert schema["servers"] == [{"url": "https://flagsmith.example.com"}]


def test_mcp_schema__full_schema_generated__includes_oauth_and_token_auth(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAGSMITH_API_URL = "https://api.flagsmith.example.com/"
    settings.FLAGSMITH_FRONTEND_URL = "https://app.flagsmith.example.com/"
    generator = MCPSchemaGenerator()

    # When
    schema = generator.get_schema(request=None, public=True)

    # Then
    assert "TOKEN_AUTH" in schema["components"]["securitySchemes"]
    assert "oauth2" in schema["components"]["securitySchemes"]
    assert schema["security"] == [{"oauth2": ["mcp"]}, {"TOKEN_AUTH": []}]
