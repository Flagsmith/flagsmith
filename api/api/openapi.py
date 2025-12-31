from typing import Any, Literal

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import ResolvedComponent
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema


class _GenerateJsonSchema(GenerateJsonSchema):
    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """Generates an OpenAPI 3.0-compatible JSON schema that allows null values.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        anyof_schema_value = super().nullable_schema(schema)
        elem = next(
            any_of
            for any_of in anyof_schema_value["anyOf"]
            if any_of.get("type") != "null"
        )
        if type_ := elem.get("type"):
            return {"type": type_, "nullable": True}
        # Assuming a reference here (which we can not annotate)
        return elem  # type: ignore[no-any-return]


class PydanticSchemaExtension(
    OpenApiSerializerExtension  # type: ignore[no-untyped-call]
):
    """
    An OpenAPI extension that allows drf-spectacular to generate schema documentation
    from Pydantic models.

    This extension is automatically used when a Pydantic BaseModel subclass is passed
    as a response type in @extend_schema decorators.
    """

    target_class = "pydantic.BaseModel"
    match_subclasses = True

    def get_name(
        self,
        auto_schema: AutoSchema | None = None,
        direction: Literal["request", "response"] | None = None,
    ) -> str | None:
        return self.target.__name__  # type: ignore[no-any-return]

    def map_serializer(
        self,
        auto_schema: AutoSchema,
        direction: str,
    ) -> dict[str, Any]:
        model_cls: type[BaseModel] = self.target

        model_json_schema = model_cls.model_json_schema(
            mode="serialization",
            schema_generator=_GenerateJsonSchema,
            ref_template="#/components/schemas/{model}",
        )

        # Register nested definitions as components
        if "$defs" in model_json_schema:
            for ref_name, schema_kwargs in model_json_schema.pop("$defs").items():
                # Mark nested models as nullable (same behaviour as the old implementation)
                schema_kwargs["nullable"] = True
                component = ResolvedComponent(  # type: ignore[no-untyped-call]
                    name=ref_name,
                    type=ResolvedComponent.SCHEMA,
                    object=ref_name,
                    schema=schema_kwargs,
                )
                auto_schema.registry.register_on_missing(component)

        return model_json_schema


def resolve_pydantic_schema(
    auto_schema: AutoSchema,
    model_cls: type[BaseModel],
) -> dict[str, Any]:
    """
    Utility function to resolve a Pydantic model to an OpenAPI schema.

    This can be used when you need to manually build a schema that includes
    Pydantic models.

    Args:
        auto_schema: The AutoSchema instance from drf-spectacular.
        model_cls: The Pydantic model class to resolve.

    Returns:
        The OpenAPI schema dictionary.
    """
    model_json_schema = model_cls.model_json_schema(
        mode="serialization",
        schema_generator=_GenerateJsonSchema,
        ref_template="#/components/schemas/{model}",
    )

    # Register nested definitions as components
    if "$defs" in model_json_schema:
        for ref_name, schema_kwargs in model_json_schema.pop("$defs").items():
            schema_kwargs["nullable"] = True
            component = ResolvedComponent(  # type: ignore[no-untyped-call]
                name=ref_name,
                type=ResolvedComponent.SCHEMA,
                object=ref_name,
                schema=schema_kwargs,
            )
            auto_schema.registry.register_on_missing(component)

    return model_json_schema
