import json

from rest_framework import serializers

from .models import FeatureExternalResource


class FeatureExternalResourceSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]

    metadata = serializers.JSONField(required=False, allow_null=True, default=None)

    class Meta:
        model = FeatureExternalResource
        fields = (
            "id",
            "url",
            "type",
            "metadata",
            "feature",
        )

    def validate_metadata(self, value) -> str:  # type: ignore[no-untyped-def]
        metadata_json = json.dumps(value)
        return metadata_json

    def to_representation(self, instance):  # type: ignore[no-untyped-def]
        representation = super().to_representation(instance)
        if "metadata" in representation and isinstance(representation["metadata"], str):
            metadata_json = representation.pop("metadata")
            representation["metadata"] = (
                json.loads(metadata_json) if metadata_json else None
            )
        return representation
