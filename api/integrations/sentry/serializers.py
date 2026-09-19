from integrations.common.serializers import BaseEnvironmentIntegrationModelSerializer

from .models import SentryChangeTrackingConfiguration


class SentryChangeTrackingConfigurationSerializer(
    BaseEnvironmentIntegrationModelSerializer
):
    class Meta:
        model = SentryChangeTrackingConfiguration
        fields = ["id", "environment", "webhook_url", "secret", "latest_health"]
        read_only_fields = ["id", "environment"]
