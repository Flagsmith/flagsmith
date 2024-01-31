import typing

from django.forms import model_to_dict
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from projects.serializers import ProjectListSerializer
from users.serializers import UserListSerializer


class AuditLogListSerializer(serializers.ModelSerializer):
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
            "related_object_type",
            "is_system_event",
        )


class AuditLogChangeDetailsSerializer(serializers.Serializer):
    field = serializers.ReadOnlyField()
    old = serializers.ReadOnlyField()
    new = serializers.ReadOnlyField()


class AuditLogRetrieveSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectListSerializer()
    change_details = serializers.SerializerMethodField()
    change_type = serializers.SerializerMethodField()
    new_instance = serializers.SerializerMethodField()
    previous_instance = serializers.SerializerMethodField()

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
            "is_system_event",
            "change_details",
            "change_type",
            "new_instance",
            "previous_instance",
        )

    @swagger_serializer_method(
        serializer_or_field=AuditLogChangeDetailsSerializer(many=True)
    )
    def get_change_details(
        self, instance: AuditLog
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        if history_record := instance.history_record:
            return AuditLogChangeDetailsSerializer(
                instance=history_record.get_change_details(), many=True
            ).data

        return []

    def get_change_type(self, instance: AuditLog) -> str:
        if not (history_record := instance.history_record):
            return "UNKNOWN"

        return {
            "+": "CREATE",
            "-": "DELETE",
            "~": "UPDATE",
        }.get(history_record.history_type)

    def get_new_instance(self, instance: AuditLog) -> dict[str, typing.Any] | None:
        if history_record := instance.history_record:
            return model_to_dict(history_record.instance)
        return None

    def get_previous_instance(self, instance: AuditLog) -> dict[str, typing.Any] | None:
        if (history_record := instance.history_record) and (
            prev_record := history_record.prev_record
        ):
            return model_to_dict(prev_record)
        return None


class AuditLogsQueryParamSerializer(serializers.Serializer):
    project = serializers.IntegerField(required=False)
    environments = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    is_system_event = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )
    search = serializers.CharField(max_length=256, required=False)
