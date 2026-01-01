import pydantic
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema

from api.openapi import PydanticSchemaExtension, resolve_pydantic_schema


def test_pydantic_schema_extension__renders_expected() -> None:
    # Given
    class Nested(pydantic.BaseModel):
        usual_str: str
        optional_int: int | None = None

    class ResponseModel(pydantic.BaseModel):
        nested_once: Nested
        nested_list: list[Nested]

    # Create an extension instance targeting the ResponseModel
    extension = PydanticSchemaExtension(  # type: ignore[no-untyped-call]
        target=ResponseModel,
    )

    # Create a mock AutoSchema with a registry
    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    schema = extension.map_serializer(auto_schema, direction="response")

    # Then
    assert schema["title"] == "ResponseModel"
    assert schema["type"] == "object"
    assert "nested_once" in schema["properties"]
    assert "nested_list" in schema["properties"]
    assert schema["required"] == ["nested_once", "nested_list"]

    # Check nested_list is an array with reference
    assert schema["properties"]["nested_list"]["type"] == "array"
    assert "$ref" in schema["properties"]["nested_list"]["items"]

    # Check nested_once is a reference
    assert "$ref" in schema["properties"]["nested_once"]


def test_pydantic_schema_extension__registers_nested_components() -> None:
    # Given
    class Nested(pydantic.BaseModel):
        usual_str: str
        optional_int: int | None = None

    class ResponseModel(pydantic.BaseModel):
        nested: Nested

    extension = PydanticSchemaExtension(  # type: ignore[no-untyped-call]
        target=ResponseModel,
    )

    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    extension.map_serializer(auto_schema, direction="response")

    # Then
    # Check that the Nested model was registered as a component
    registered_schemas = {
        component.name for component in auto_schema.registry._components.values()
    }
    assert "Nested" in registered_schemas


def test_pydantic_schema_extension__get_name() -> None:
    # Given
    class MyModel(pydantic.BaseModel):
        field: str

    extension = PydanticSchemaExtension(  # type: ignore[no-untyped-call]
        target=MyModel,
    )

    # When
    name = extension.get_name()

    # Then
    assert name == "MyModel"


def test_resolve_pydantic_schema__renders_expected() -> None:
    # Given
    class Nested(pydantic.BaseModel):
        usual_str: str
        optional_int: int | None = None

    class ResponseModel(pydantic.BaseModel):
        nested: Nested

    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    schema = resolve_pydantic_schema(auto_schema, ResponseModel)

    # Then
    assert schema["title"] == "ResponseModel"
    assert schema["type"] == "object"
    assert "nested" in schema["properties"]

    # Check that the Nested model was registered as a component
    registered_schemas = {
        component.name for component in auto_schema.registry._components.values()
    }
    assert "Nested" in registered_schemas
