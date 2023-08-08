from rest_framework import serializers


class LaunchDarklyImportSerializer(serializers.Serializer):
    api_key = serializers.CharField(required=True)
    organisation_id = serializers.IntegerField(required=True)
    project_id = serializers.IntegerField(required=False, allow_null=True)
    ld_project_id = serializers.CharField(required=True)
