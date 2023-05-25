from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from integrations.heap.models import HeapConfiguration


class HeapConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = HeapConfiguration
        fields = ("id", "api_key")
