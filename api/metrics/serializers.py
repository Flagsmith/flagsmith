from rest_framework import serializers


class FeaturesMetricsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    enabled = serializers.IntegerField()
    
class SegmentMetricsSerializer(serializers.Serializer):
    overrides = serializers.IntegerField()

class IdentityMetricsSerializer(serializers.Serializer):
    overrides = serializers.IntegerField()

class EnvironmentMetricsSerializer(serializers.Serializer):
    features = FeaturesMetricsSerializer()
    segment = SegmentMetricsSerializer()