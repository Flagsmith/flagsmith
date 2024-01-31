from rest_framework import serializers

from .models import ExternalResources, FeatureExternalResources


class ExternalResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalResources
        fields = (
            "id",
            "url",
            "type",
            "resources_id",
            "project",
        )


class FeatureExternalResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureExternalResources
        fields = ("id", "feature", "external_resource")
        read_only_fields = ("external_resource",)
