from rest_framework import serializers

from integrations.segment.models import SegmentConfiguration


class SegmentConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentConfiguration
        fields = ("id", "api_key")
