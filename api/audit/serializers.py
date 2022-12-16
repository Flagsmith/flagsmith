import typing

from drf_yasg2.utils import swagger_serializer_method
from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from projects.serializers import ProjectSerializer
from users.serializers import UserListSerializer


class AuditLogListSerializer(serializers.ModelSerializer):
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
            "is_system_event",
        )


class AuditLogChangeDetailsSerializer(serializers.Serializer):
    field = serializers.ReadOnlyField()
    old = serializers.ReadOnlyField()
    new = serializers.ReadOnlyField()


class AuditLogRetrieveSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectSerializer()
    change_details = serializers.SerializerMethodField()

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
        )

    @swagger_serializer_method(
        serializer_or_field=AuditLogChangeDetailsSerializer(many=True)
    )
    def get_change_details(self, instance) -> typing.List[typing.Dict]:
        return AuditLogChangeDetailsSerializer(
            instance=instance.history_record.get_change_details(), many=True
        ).data


class AuditLogsQueryParamSerializer(serializers.Serializer):
    project = serializers.IntegerField(required=False)
    environments = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    is_system_event = serializers.BooleanField(required=False)
    search = serializers.CharField(max_length=256, required=False)
