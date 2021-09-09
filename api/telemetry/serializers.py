from app_analytics import InfluxDBWrapper
from core.helpers import get_ip_address_from_request
from django.conf import settings
from rest_framework import serializers


class TelemetrySerializer(serializers.Serializer):
    organisations = serializers.IntegerField()
    projects = serializers.IntegerField()
    environments = serializers.IntegerField()
    features = serializers.IntegerField()
    segments = serializers.IntegerField()
    users = serializers.IntegerField()
    debug_enabled = serializers.BooleanField()
    env = serializers.CharField()

    def save(self, instance=None):
        if settings.INFLUXDB_TOKEN:
            influxdb = InfluxDBWrapper("self_hosted_telemetry")
            tags = {
                **self.validated_data,
                "ip_address": get_ip_address_from_request(self.context["request"]),
            }
            influxdb.add_data_point("heartbeat", 1, tags=tags)
            influxdb.write()
