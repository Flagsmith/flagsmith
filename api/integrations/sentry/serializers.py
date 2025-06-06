from integrations.common.serializers import BaseEnvironmentIntegrationModelSerializer

from .models import SentryChangeTrackingConfiguration


class SentryChangeTrackingConfigurationSerializer(
    BaseEnvironmentIntegrationModelSerializer
):
    class Meta:
        model = SentryChangeTrackingConfiguration
        fields = ["pk", "environment", "webhook_url", "secret"]
        read_only_fields = ["pk", "environment"]
