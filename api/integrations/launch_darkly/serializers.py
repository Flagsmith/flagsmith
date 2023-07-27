from rest_framework import serializers


class LaunchDarklyImportSerializer(serializers.Serializer):
    api_key = serializers.CharField(required=True)
    organisation_id = serializers.UUIDField(required=True)
    project_id = serializers.UUIDField(required=False)
    ld_project_id = serializers.CharField(required=True)
