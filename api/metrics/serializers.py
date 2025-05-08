from rest_framework import serializers


class MetricItemSerializer(
    serializers.Serializer[dict[str, int | str | bool | int | None]]
):
    value = serializers.IntegerField()
    description = serializers.CharField()
    name = serializers.CharField()
    entity = serializers.CharField()
    rank = serializers.IntegerField(required=False)


class EnvironmentMetricsSerializer(
    serializers.Serializer[dict[str, list[MetricItemSerializer]]]
):
    metrics = MetricItemSerializer(many=True)
