import re

from rest_framework import serializers

from integrations.common.serializers import (
    BaseProjectIntegrationModelSerializer,
)

from .models import DiscordConfiguration

DISCORD_WEBHOOK_URL = re.compile(
    r"^https://(?:(?:canary|ptb)\.)?discord(?:app)?\.com/api/(?:v\d+/)?webhooks/\d+/[\w-]+/?$"
)


class DiscordConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    base_url = serializers.CharField(
        help_text="The Discord channel webhook URL (Server Settings > Integrations > Webhooks)."
    )

    class Meta:
        model = DiscordConfiguration
        fields = ("id", "base_url")

    def validate_base_url(self, value: str) -> str:
        if not DISCORD_WEBHOOK_URL.match(value):
            raise serializers.ValidationError(
                "Enter a Discord webhook URL, e.g. https://discord.com/api/webhooks/<id>/<token>."
            )
        return value
