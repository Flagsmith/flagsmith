from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)

from .models import GrafanaConfiguration


class GrafanaConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = GrafanaConfiguration
        fields = ("id", "base_url", "api_key")
