from rest_framework import serializers


class MetricItemSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    description = serializers.CharField()
    title = serializers.CharField()
    disabled = serializers.BooleanField(default=False)


class EnvironmentMetricsSerializer(serializers.Serializer):
    features = MetricItemSerializer(many=True)
    segments = MetricItemSerializer(many=True)
    change_requests = MetricItemSerializer(many=True, required=False)
    scheduled_changes = MetricItemSerializer(many=True, required=False)
