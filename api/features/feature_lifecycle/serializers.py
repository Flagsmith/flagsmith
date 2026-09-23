from rest_framework import serializers


class FeatureLifecycleCountsSerializer(serializers.Serializer[dict[str, int]]):
    """Number of features in each lifecycle stage for an environment"""

    new = serializers.IntegerField()
    live = serializers.IntegerField()
    stale = serializers.IntegerField()
    permanent = serializers.IntegerField()
    needs_monitoring = serializers.IntegerField()
    to_remove = serializers.IntegerField()
