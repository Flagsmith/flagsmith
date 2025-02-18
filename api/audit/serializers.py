import typing

from drf_yasg.utils import swagger_serializer_method  # type: ignore[import-untyped]
from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from projects.serializers import ProjectListSerializer
from users.serializers import UserListSerializer


class AuditLogListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectListSerializer()

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
            "related_object_uuid",
            "related_object_type",
            "is_system_event",
        )


class AuditLogChangeDetailsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    field = serializers.ReadOnlyField()
    old = serializers.ReadOnlyField()
    new = serializers.ReadOnlyField()


class AuditLogRetrieveSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectListSerializer()
    change_details = serializers.SerializerMethodField()
    change_type = serializers.SerializerMethodField()

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
            "related_object_uuid",
            "related_object_type",
            "is_system_event",
            "change_details",
            "change_type",
        )

    @swagger_serializer_method(  # type: ignore[misc]
        serializer_or_field=AuditLogChangeDetailsSerializer(many=True)
    )
    def get_change_details(
        self, instance: AuditLog
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        if history_record := instance.history_record:
            return AuditLogChangeDetailsSerializer(  # type: ignore[return-value]
                instance=history_record.get_change_details(), many=True  # type: ignore[attr-defined]
            ).data

        return []

    def get_change_type(self, instance: AuditLog) -> str:
        if not (history_record := instance.history_record):
            return "UNKNOWN"

        return {  # type: ignore[return-value]
            "+": "CREATE",
            "-": "DELETE",
            "~": "UPDATE",
        }.get(
            history_record.history_type  # type: ignore[attr-defined]
        )


class AuditLogsQueryParamSerializer(serializers.Serializer):  # type: ignore[type-arg]
    project = serializers.IntegerField(required=False)
    environments = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    is_system_event = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )
    search = serializers.CharField(max_length=256, required=False)
