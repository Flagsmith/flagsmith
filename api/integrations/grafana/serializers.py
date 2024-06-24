from integrations.common.serializers import (
    BaseProjectIntegrationModelSerializer,
)

from .models import GrafanaConfiguration


class GrafanaConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = GrafanaConfiguration
        fields = ("id", "base_url", "api_key")
