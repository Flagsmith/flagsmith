from rest_framework import serializers


class FeaturesMetricsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    enabled = serializers.IntegerField()
    
class SegmentMetricsSerializer(serializers.Serializer):
    overrides = serializers.IntegerField()
    enabled = serializers.IntegerField()

class IdentityMetricsSerializer(serializers.Serializer):
    overrides = serializers.IntegerField()

class ChangeRequestMetricsSerializer(serializers.Serializer):
    open = serializers.IntegerField()

class ScheduledChangeMetricsSerializer(serializers.Serializer):
    total = serializers.IntegerField()

class EnvironmentMetricsSerializer(serializers.Serializer):
    features = FeaturesMetricsSerializer()
    segments = SegmentMetricsSerializer()
    change_requests = ChangeRequestMetricsSerializer(required=False)
    scheduled_changes = ScheduledChangeMetricsSerializer(required=False)