import inspect
from typing import Any

from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.openapi import SCHEMA_DEFINITIONS, Response, Schema
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema


class _GenerateJsonSchema(GenerateJsonSchema):
    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """Generates an OpenAPI 2.0-compatible JSON schema that matches a schema that allows null values.

        (The catch is OpenAPI 2.0 does not allow them, but some clients are capable
        to consume the `x-nullable` annotation.)

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
        if type := elem.get("type"):
            return {"type": type, "x-nullable": True}
        # Assuming a reference here (which we can not annotate)
        return elem


class PydanticResponseCapableSwaggerAutoSchema(SwaggerAutoSchema):
    """
    A `SwaggerAutoSchema` subclass that allows to generate view response Swagger docs
    from a Pydantic model.

    Example usage:

    ```
    @drf_yasg.utils.swagger_auto_schema(
        responses={200: YourPydanticSchema},
        auto_schema=PydanticResponseCapableSwaggerAutoSchema,
    )
    def your_view(): ...
    ```

    To adapt Pydantic-generated schemas, the following is taken care of:

    1. Pydantic-generated definitions are unwrapped and added to drf-yasg's global definitions.
    2. Rather than using `anyOf`, nullable fields are annotated with `x-nullable`.
    3. As there's no way to annotate a reference, all nested models are assumed to be `x-nullable`.
    """

    def get_response_schemas(
        self,
        response_serializers: dict[str | int, Any],
    ) -> dict[str, Response]:
        result = {}

        definitions = self.components.with_scope(SCHEMA_DEFINITIONS)

        for status_code in list(response_serializers):
            if inspect.isclass(response_serializers[status_code]) and issubclass(
                model_cls := response_serializers[status_code], BaseModel
            ):
                model_json_schema = model_cls.model_json_schema(
                    mode="serialization",
                    schema_generator=_GenerateJsonSchema,
                    ref_template=f"#/{SCHEMA_DEFINITIONS}/{{model}}",
                )

                for ref_name, schema_kwargs in model_json_schema.pop("$defs").items():
                    definitions.setdefault(
                        ref_name,
                        maker=lambda: Schema(
                            **schema_kwargs,
                            # We can not annotate references with `x-nullable`,
                            # So just assume all nested models as nullable for now.
                            x_nullable=True,
                        ),
                    )

                result[str(status_code)] = Response(
                    description=model_cls.__name__,
                    schema=Schema(**model_json_schema),
                )

                del response_serializers[status_code]

        return {**super().get_response_schemas(response_serializers), **result}
