from rest_framework import serializers

from integrations.flagd.models import FlagdProjectConfiguration


class FlagdProjectConfigurationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = FlagdProjectConfiguration
        fields = ("enabled", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")
