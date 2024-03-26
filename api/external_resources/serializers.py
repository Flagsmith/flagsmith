from rest_framework import serializers

from .models import ExternalResources


class ExternalResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalResources
        fields = (
            "id",
            "url",
            "type",
            "status",
            "feature",
        )
