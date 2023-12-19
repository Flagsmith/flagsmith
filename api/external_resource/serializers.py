from rest_framework import serializers

from external_resource.models import ExternalResource, FeatureExternalResource


class ExternalResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalResource
        fields = ["id", "url", "type"]


class FeatureExternalResourceSerializer(serializers.ModelSerializer):
    external_resource = ExternalResourceSerializer()

    class Meta:
        model = FeatureExternalResource
        fields = ["id", "external_resource", "feature"]
