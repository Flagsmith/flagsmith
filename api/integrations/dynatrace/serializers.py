from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)

from .models import DynatraceConfiguration


class DynatraceConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = DynatraceConfiguration
        fields = ("id", "base_url", "api_key", "entity_selector")
