from typing import Any

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema


class TraitValueFieldExtension(OpenApiSerializerFieldExtension):  # type: ignore[no-untyped-call]
    target_class = "environments.identities.traits.fields.TraitValueField"

    def map_serializer_field(
        self, auto_schema: AutoSchema, direction: str
    ) -> dict[str, Any]:
        return {
            "type": [
                "string",
                "integer",
                "number",
                "boolean",
            ],
            "description": "Can be string, integer, float, or boolean",
        }
