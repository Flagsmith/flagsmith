from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from integrations.rudderstack.models import RudderstackConfiguration


class RudderstackConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = RudderstackConfiguration
        fields = ("id", "base_url", "api_key")
