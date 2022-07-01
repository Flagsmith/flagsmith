from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from projects.serializers import ProjectSerializer
from users.serializers import UserListSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectSerializer()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "created_date",
            "log",
            "author",
            "environment",
            "project",
            "related_object_id",
            "related_object_type",
        )


class AuditLogsQueryParamSerializer(serializers.Serializer):
    project = serializers.IntegerField(required=False)
    environments = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    search = serializers.CharField(max_length=256, required=False)
