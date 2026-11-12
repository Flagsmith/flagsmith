from integrations.common.serializers import (
    BaseProjectIntegrationModelSerializer,
)

from .models import NewRelicConfiguration


class NewRelicConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = NewRelicConfiguration
        fields = ("id", "base_url", "api_key", "app_id")
