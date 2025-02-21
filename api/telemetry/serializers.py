from django.conf import settings
from rest_framework import serializers

from app_analytics.influxdb_wrapper import InfluxDBWrapper
from core.helpers import get_ip_address_from_request


class TelemetrySerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisations = serializers.IntegerField()
    projects = serializers.IntegerField()
    environments = serializers.IntegerField()
    features = serializers.IntegerField()
    segments = serializers.IntegerField()
    users = serializers.IntegerField()
    debug_enabled = serializers.BooleanField()
    env = serializers.CharField()

    def save(self, instance=None):  # type: ignore[no-untyped-def,override]
        if settings.INFLUXDB_TOKEN:
            influxdb = InfluxDBWrapper("self_hosted_telemetry")  # type: ignore[no-untyped-call]
            tags = {
                **self.validated_data,
                "ip_address": get_ip_address_from_request(self.context["request"]),  # type: ignore[no-untyped-call]
            }
            influxdb.add_data_point("heartbeat", 1, tags=tags)  # type: ignore[no-untyped-call]
            influxdb.write()  # type: ignore[no-untyped-call]
