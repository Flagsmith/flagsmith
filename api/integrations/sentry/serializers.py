from integrations.common.serializers import BaseEnvironmentIntegrationModelSerializer
from webhooks.fields import NoSSRFURLField

from .models import SentryChangeTrackingConfiguration


class SentryChangeTrackingConfigurationSerializer(
    BaseEnvironmentIntegrationModelSerializer
):
    webhook_url = NoSSRFURLField()

    class Meta:
        model = SentryChangeTrackingConfiguration
        fields = ["id", "environment", "webhook_url", "secret"]
        read_only_fields = ["id", "environment"]
