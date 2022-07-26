from rest_framework import serializers


class MonitoringSerializer(serializers.Serializer):
    waiting = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    failed = serializers.IntegerField(read_only=True)
