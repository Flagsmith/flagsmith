from rest_framework import serializers


class EdgeIdentityTraitsResponseSerializer(serializers.Serializer):
    trait_key = serializers.CharField()
    trait_value = serializers.CharField(allow_null=True)
