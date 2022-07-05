from django.conf import settings
from rest_framework import serializers

from environments.dynamodb.migrator import IdentityMigrator
from environments.dynamodb.types import ProjectIdentityMigrationStatus
from permissions.serializers import CreateUpdateUserPermissionSerializerABC
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.serializers import (
    UserListSerializer,
    UserPermissionGroupSerializerList,
)


class ProjectSerializer(serializers.ModelSerializer):
    migration_status = serializers.SerializerMethodField(
        help_text="Edge migration status of the project; can be one of: "
        + ", ".join([k.value for k in ProjectIdentityMigrationStatus])
    )

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "organisation",
            "hide_disabled_flags",
            "enable_dynamo_db",
            "migration_status",
        )

    def get_migration_status(self, obj: Project) -> str:
        if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            return ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED.value
        if (
            settings.EDGE_RELEASE_DATETIME
            and obj.created_date >= settings.EDGE_RELEASE_DATETIME
        ):
            return ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value

        identity_migrator = IdentityMigrator(obj.id)
        return identity_migrator.migration_status.value


class CreateUpdateUserProjectPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("user",)


class ListUserProjectPermissionSerializer(CreateUpdateUserProjectPermissionSerializer):
    user = UserListSerializer()


class CreateUpdateUserPermissionGroupProjectPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserPermissionGroupProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("group",)


class ListUserPermissionGroupProjectPermissionSerializer(
    CreateUpdateUserPermissionGroupProjectPermissionSerializer
):
    group = UserPermissionGroupSerializerList()
