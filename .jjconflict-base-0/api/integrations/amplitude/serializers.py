from integrations.amplitude.models import AmplitudeConfiguration
from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)


class AmplitudeConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = AmplitudeConfiguration
        fields = ("id", "api_key", "base_url")
