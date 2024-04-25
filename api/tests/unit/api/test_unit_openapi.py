import pydantic
from drf_yasg.openapi import (
    SCHEMA_DEFINITIONS,
    ReferenceResolver,
    Response,
    Schema,
)
from pytest_mock import MockerFixture

from api.openapi import PydanticResponseCapableSwaggerAutoSchema


def test_pydantic_response_capable_auto_schema__renders_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    class Nested(pydantic.BaseModel):
        usual_str: str
        optional_int: int | None = None

    class ResponseModel(pydantic.BaseModel):
        nested_once: Nested
        nested_list: list[Nested]

    auto_schema = PydanticResponseCapableSwaggerAutoSchema(
        view=mocker.MagicMock(),
        path=mocker.MagicMock(),
        method=mocker.MagicMock(),
        components=ReferenceResolver("definitions", force_init=True),
        request=mocker.MagicMock(),
        overrides=mocker.MagicMock(),
    )

    # When
    response_schemas = auto_schema.get_response_schemas({200: ResponseModel})

    # Then
    assert response_schemas == {
        "200": Response(
            description="ResponseModel",
            schema=Schema(
                title="ResponseModel",
                required=["nested_once", "nested_list"],
                type="object",
                properties={
                    "nested_list": {
                        "items": {"$ref": "#/definitions/Nested"},
                        "title": "Nested List",
                        "type": "array",
                    },
                    "nested_once": {"$ref": "#/definitions/Nested"},
                },
            ),
        ),
    }
    nested_schema = auto_schema.components.with_scope(SCHEMA_DEFINITIONS).get("Nested")
    assert nested_schema == Schema(
        title="Nested",
        required=["usual_str"],
        type="object",
        properties={
            "optional_int": {
                "default": None,
                "title": "Optional Int",
                "type": "integer",
                "x-nullable": True,
            },
            "usual_str": {"title": "Usual Str", "type": "string"},
        },
        x_nullable=True,
    )
