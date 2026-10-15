from rest_framework import serializers


class ChangeRequestReferenceSerializer(serializers.Serializer[None]):
    change_request = serializers.IntegerField()
