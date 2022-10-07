from rest_framework import serializers


class MonitoringSerializer(serializers.Serializer):
    waiting = serializers.IntegerField(read_only=True)
