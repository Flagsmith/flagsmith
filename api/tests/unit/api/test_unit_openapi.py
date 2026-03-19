from typing import Any

import pytest
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from typing_extensions import TypedDict

from api.openapi import (
    TAGS,
    TypedDictSchemaExtension,
    postprocessing_assign_tags,
    preprocessing_filter_spec,
)


def test_typeddict_schema_extension__renders_expected() -> None:
    # Given
    class Nested(TypedDict):
        usual_str: str
        optional_int: int | None

    class ResponseModel(TypedDict):
        nested_once: Nested
        nested_list: list[Nested]

    # Create an extension instance targeting the ResponseModel
    extension = TypedDictSchemaExtension(  # type: ignore[no-untyped-call]
        target=ResponseModel,
    )

    # Create a mock AutoSchema with a registry
    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    schema = extension.map_serializer(auto_schema, direction="response")

    # Then
    assert schema == {
        "properties": {
            "nested_list": {
                "items": {"$ref": "#/components/schemas/ResponseModelNested"},
                "title": "Nested List",
                "type": "array",
            },
            "nested_once": {"$ref": "#/components/schemas/ResponseModelNested"},
        },
        "required": ["nested_once", "nested_list"],
        "title": "ResponseModel",
        "type": "object",
    }


def test_typeddict_schema_extension__registers_nested_components() -> None:
    # Given
    class Nested(TypedDict):
        usual_str: str
        optional_int: int | None

    class ResponseModel(TypedDict):
        nested: Nested

    extension = TypedDictSchemaExtension(  # type: ignore[no-untyped-call]
        target=ResponseModel,
    )

    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    extension.map_serializer(auto_schema, direction="response")
    schema = auto_schema.registry.build({})

    # Then
    # the Nested model was registered as a component
    # with a prefixed name
    assert schema == {
        "schemas": {
            "ResponseModelNested": {
                "properties": {
                    "optional_int": {
                        "anyOf": [{"type": "integer"}, {"type": "null"}],
                        "title": "Optional Int",
                    },
                    "usual_str": {"title": "Usual Str", "type": "string"},
                },
                "required": ["usual_str", "optional_int"],
                "title": "Nested",
                "type": "object",
            }
        },
    }


@pytest.mark.parametrize(
    "path, expected_tag",
    [
        ("/api/v1/organisations/", "Organisations"),
        ("/api/v1/organisations/{id}/groups/", "Organisations"),
        ("/api/v1/projects/{id}/", "Projects"),
        ("/api/v1/environments/{api_key}/", "Environments"),
        ("/api/v1/projects/{id}/features/", "Features"),
        ("/api/v1/flags/{feature_id}/multivariate-options/", "Features"),
        ("/api/v1/environments/{api_key}/featurestates/{id}/", "Feature states"),
        ("/api/v1/environment-feature-versions/{id}/", "Feature states"),
        ("/api/v1/environments/{api_key}/identities/{id}/", "Identities"),
        ("/api/v1/environments/{api_key}/edge-identities/{id}/", "Identities"),
        ("/api/v1/traits/", "Identities"),
        ("/api/v1/segments/{id}/", "Segments"),
        ("/api/v1/environments/{api_key}/integrations/amplitude/{id}/", "Integrations"),
        ("/api/v1/projects/{id}/integrations/datadog/{id}/", "Integrations"),
        ("/api/v1/organisations/{id}/integrations/github/", "Integrations"),
        ("/api/v1/environments/{api_key}/user-permissions/{id}/", "Permissions"),
        ("/api/v1/projects/{id}/user-group-permissions/{id}/", "Permissions"),
        ("/api/v1/environments/{api_key}/webhooks/{id}/", "Webhooks"),
        ("/api/v1/cb-webhook/", "Webhooks"),
        ("/api/v1/github-webhook/", "Webhooks"),
        ("/api/v1/audit/", "Audit"),
        ("/api/v1/auth/login/", "Authentication"),
        ("/api/v1/users/join/{hash}/", "Authentication"),
        ("/api/v1/analytics/flags/", "Analytics"),
        ("/api/v1/metadata/fields/", "Metadata"),
        ("/api/v1/onboarding/request/send/", "Onboarding"),
        ("/api/v1/admin/dashboard/summary/", "Admin dashboard"),
    ],
)
def test_postprocessing_assign_tags__assigns_correct_tag(
    path: str, expected_tag: str
) -> None:
    # Given
    result: dict[str, Any] = {
        "paths": {
            path: {
                "get": {
                    "operationId": "test_op",
                    "tags": ["api"],
                },
            },
        },
    }

    # When
    postprocessing_assign_tags(result, generator=None)

    # Then
    assert result["paths"][path]["get"]["tags"] == [expected_tag]


def test_postprocessing_assign_tags__preserves_explicit_tags() -> None:
    # Given
    result: dict[str, Any] = {
        "paths": {
            "/api/v1/flags/": {
                "get": {
                    "operationId": "sdk_flags",
                    "tags": ["sdk"],
                },
            },
            "/api/v1/organisations/": {
                "get": {
                    "operationId": "organisations_list",
                    "tags": ["mcp", "organisations"],
                },
            },
        },
    }

    # When
    postprocessing_assign_tags(result, generator=None)

    # Then
    assert result["paths"]["/api/v1/flags/"]["get"]["tags"] == ["sdk"]
    assert result["paths"]["/api/v1/organisations/"]["get"]["tags"] == [
        "mcp",
        "organisations",
    ]


def test_postprocessing_assign_tags__sets_tags_list_on_result() -> None:
    # Given
    result: dict[str, Any] = {"paths": {}}

    # When
    postprocessing_assign_tags(result, generator=None)

    # Then
    assert result["tags"] == TAGS


def test_postprocessing_assign_tags__unmatched_path_gets_other_tag() -> None:
    # Given
    result: dict[str, Any] = {
        "paths": {
            "/api/v1/unknown-endpoint/": {
                "get": {
                    "operationId": "unknown",
                    "tags": ["api"],
                },
            },
        },
    }

    # When
    postprocessing_assign_tags(result, generator=None)

    # Then
    assert result["paths"]["/api/v1/unknown-endpoint/"]["get"]["tags"] == ["Other"]


def test_preprocessing_filter_spec__removes_swagger_endpoints() -> None:
    # Given
    endpoints = [
        ("/api/v1/organisations/", "^api/v1/organisations/", "GET", None),
        ("/api/v1/swagger.json", "^api/v1/swagger.json", "GET", None),
        ("/api/v1/swagger.yaml", "^api/v1/swagger.yaml", "GET", None),
    ]

    # When
    filtered = preprocessing_filter_spec(endpoints)

    # Then
    assert len(filtered) == 1
    assert filtered[0][0] == "/api/v1/organisations/"


def test_typeddict_schema_extension__get_name() -> None:
    # Given
    class MyModel(TypedDict):
        field: str

    extension = TypedDictSchemaExtension(  # type: ignore[no-untyped-call]
        target=MyModel,
    )

    # When
    name = extension.get_name()

    # Then
    assert name == "MyModel"
