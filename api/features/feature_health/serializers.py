from rest_framework import serializers

from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthProvider,
    FeatureHealthProviderName,
)
from features.feature_health.providers.services import (
    get_webhook_path_from_provider,
)


class FeatureHealthEventSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = FeatureHealthEvent
        fields = read_only_fields = (
            "created_at",
            "environment",
            "feature",
            "provider_name",
            "reason",
            "type",
        )


class FeatureHealthProviderSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    created_by = serializers.SlugRelatedField(slug_field="email", read_only=True)  # type: ignore[var-annotated]
    webhook_url = serializers.SerializerMethodField()

    def get_webhook_url(self, instance: FeatureHealthProvider) -> str:
        request = self.context["request"]
        path = get_webhook_path_from_provider(instance)
        return request.build_absolute_uri(path)  # type: ignore[no-any-return]

    class Meta:
        model = FeatureHealthProvider
        fields = (
            "created_by",
            "name",
            "project",
            "webhook_url",
        )


class CreateFeatureHealthProviderSerializer(serializers.Serializer):  # type: ignore[type-arg]
    name = serializers.ChoiceField(choices=FeatureHealthProviderName.choices)
