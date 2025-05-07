from rest_framework import serializers


class MetricItemSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    description = serializers.CharField()
    name = serializers.CharField()
    disabled = serializers.BooleanField(default=False)
    entity = serializers.CharField()
    rank = serializers.IntegerField(required=False)

class EnvironmentMetricsSerializer(serializers.Serializer):
    metrics = MetricItemSerializer(many=True)