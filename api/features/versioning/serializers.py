from rest_framework.serializers import ModelSerializer

from features.versioning.models import EnvironmentFeatureVersion


class EnvironmentFeatureVersionSerializer(ModelSerializer):
    class Meta:
        model = EnvironmentFeatureVersion
        fields = ("created_at", "updated_at", "published", "live_from", "sha")
        read_only_fields = ("published", "updated_at", "created_at", "sha")
