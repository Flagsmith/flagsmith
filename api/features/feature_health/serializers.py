from rest_framework import serializers

from features.feature_health.models import (
    FeatureHealthProvider,
    FeatureHealthProviderType,
)
from features.feature_health.services import get_webhook_path_from_provider


class FeatureHealthProviderSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field="email", read_only=True)
    webhook_url = serializers.SerializerMethodField()

    def get_webhook_url(self, instance: FeatureHealthProvider) -> str:
        request = self.context["request"]
        path = get_webhook_path_from_provider(instance, self.context["request"])
        return request.build_absolute_uri(path)

    class Meta:
        model = FeatureHealthProvider
        fields = (
            "uuid",
            "type",
            "project",
            "created_by",
            "webhook_url",
        )


class CreateFeatureHealthProviderSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=FeatureHealthProviderType.choices)
