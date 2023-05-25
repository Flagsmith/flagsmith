from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from integrations.segment.models import SegmentConfiguration


class SegmentConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    class Meta:
        model = SegmentConfiguration
        fields = ("id", "api_key")
