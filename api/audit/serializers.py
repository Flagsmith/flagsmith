from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from organisations.serializers import OrganisationSerializerBasic
from projects.serializers import ProjectListSerializer
from users.serializers import UserListSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    organisation = OrganisationSerializerBasic()
    environment = EnvironmentSerializerLight()
    project = ProjectListSerializer()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "created_date",
            "log",
            "author",
            "organisation",
            "environment",
            "project",
            "related_object_id",
            "related_object_type",
            "is_system_event",
        )


class AuditLogsQueryParamSerializer(serializers.Serializer):
    organisation = serializers.IntegerField(required=False)
    project = serializers.IntegerField(required=False)
    environments = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    is_system_event = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )
    search = serializers.CharField(max_length=256, required=False)
