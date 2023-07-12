from datetime import datetime

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from features.serializers import CreateSegmentOverrideFeatureStateSerializer
from features.versioning.models import EnvironmentFeatureVersion


class EnvironmentFeatureVersionFeatureStateSerializer(
    CreateSegmentOverrideFeatureStateSerializer
):
    class Meta(CreateSegmentOverrideFeatureStateSerializer.Meta):
        read_only_fields = (
            CreateSegmentOverrideFeatureStateSerializer.Meta.read_only_fields
            + ("feature",)
        )


class EnvironmentFeatureVersionSerializer(ModelSerializer):
    class Meta:
        model = EnvironmentFeatureVersion
        fields = ("created_at", "updated_at", "published", "live_from", "sha")
        read_only_fields = ("updated_at", "created_at", "sha")

    def validate_published(self, published: bool) -> None:
        if instance := getattr(self, "instance", None):
            if instance.is_live and published is False:
                raise ValidationError("Cannot un-publish already live version")

    def validate_live_from(self, live_from: datetime) -> None:
        if instance := getattr(self, "instance", None):
            if instance.is_live and live_from != instance.live_from:
                raise ValidationError(
                    "Cannot change 'live from' date of already live version."
                )
