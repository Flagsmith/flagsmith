import logging

import simplejson as json
from rest_framework import serializers

from .models import FeatureExternalResource

logger = logging.getLogger(__name__)


class FeatureExternalResourceSerializer(serializers.ModelSerializer):

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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "metadata" in representation and isinstance(representation["metadata"], str):
            metadata_json = representation.pop("metadata")
            representation["metadata"] = (
                json.loads(metadata_json) if metadata_json else None
            )
        return representation
