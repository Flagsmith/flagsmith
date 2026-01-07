from typing import Any

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema


class EdgeFeatureFieldExtension(OpenApiSerializerFieldExtension):  # type: ignore[no-untyped-call]
    target_class = "edge_api.identities.serializers.EdgeFeatureField"

    def map_serializer_field(
        self,
        auto_schema: AutoSchema,
        direction: str,
    ) -> dict[str, Any]:
        if direction == "request":
            return {
                "oneOf": [
                    {"type": "integer", "description": "Feature ID"},
                    {"type": "string", "description": "Feature name"},
                ],
                "description": "Feature identifier (ID or name)",
            }
        return {"type": "integer", "description": "Feature ID"}
