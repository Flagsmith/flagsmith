from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.types import AuditLogChangeDetail, ChangeType
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


class AuditLogChangeDetailsSerializer(serializers.Serializer[AuditLogChangeDetail]):
    field = serializers.CharField(read_only=True)
    old = serializers.ReadOnlyField(allow_null=True)
    new = serializers.ReadOnlyField(allow_null=True)


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

    @extend_schema_field(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "old": {"type": ["string", "number", "boolean", "null"]},
                    "new": {"type": ["string", "number", "boolean", "null"]},
                },
            },
        }
    )
    def get_change_details(self, instance: AuditLog) -> list[AuditLogChangeDetail]:
        if history_record := instance.history_record:
            changes = history_record.get_change_details()  # type: ignore[attr-defined]

            # For segment updates, include rule/condition diffs.
            if (
                instance.related_object_type == RelatedObjectType.SEGMENT.name
                and history_record.history_type == "~"  # type: ignore[attr-defined]
                and getattr(history_record, "version", None)
            ):
                from segments.audit_helpers import (
                    get_segment_rules_change_details,
                )

                changes = list(changes) + get_segment_rules_change_details(
                    segment_id=instance.related_object_id,  # type: ignore[arg-type]
                    current_version=history_record.version,  # type: ignore[attr-defined]
                )

            return AuditLogChangeDetailsSerializer(  # type: ignore[return-value]
                instance=changes,
                many=True,
            ).data

        return []

    def get_change_type(self, instance: AuditLog) -> ChangeType:
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
