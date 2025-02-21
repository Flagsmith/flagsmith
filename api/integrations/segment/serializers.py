from rest_framework import serializers

from integrations.common.serializers import (
    BaseEnvironmentIntegrationModelSerializer,
)
from integrations.segment import constants
from integrations.segment.models import SegmentConfiguration


class SegmentConfigurationSerializer(BaseEnvironmentIntegrationModelSerializer):
    base_url = serializers.ChoiceField(
        choices=[
            constants.DEFAULT_BASE_URL,
            constants.DUBLIN_BASE_URL,
        ],
        required=False,
        default=constants.DEFAULT_BASE_URL,
    )

    class Meta:
        model = SegmentConfiguration
        fields = ("id", "api_key", "base_url")
