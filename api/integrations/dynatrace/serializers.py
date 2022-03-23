from rest_framework import serializers

from .models import DynatraceConfiguration


class DynatraceConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynatraceConfiguration
        fields = ("id", "base_url", "api_key")
