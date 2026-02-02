from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from typing_extensions import TypedDict

from api.openapi import TypedDictSchemaExtension


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
