from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from integrations.mixpanel.models import MixpanelConfiguration


class MixpanelConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = MixpanelConfiguration
        fields = ("id", "api_key")
