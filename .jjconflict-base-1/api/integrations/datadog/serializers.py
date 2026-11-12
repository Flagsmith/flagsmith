from integrations.common.serializers import (
    BaseProjectIntegrationModelSerializer,
)

from .models import DataDogConfiguration


class DataDogConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = DataDogConfiguration
        fields = ("id", "base_url", "api_key", "use_custom_source")
