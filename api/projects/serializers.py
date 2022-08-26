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
    use_edge_identities = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "uuid",
            "name",
            "organisation",
            "hide_disabled_flags",
            "enable_dynamo_db",
            "migration_status",
            "use_edge_identities",
        )

    def get_migration_status(self, obj: Project) -> str:
        if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            migration_status = ProjectIdentityMigrationStatus.NOT_APPLICABLE.value

        elif obj.is_edge_project_by_default:
            migration_status = ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value

        else:
            migration_status = IdentityMigrator(obj.id).migration_status.value

        # Add migration status to the context - to be used by `get_use_edge_identities`
        self.context["migration_status"] = migration_status

        return migration_status

    def get_use_edge_identities(self, obj: Project) -> bool:
        return (
            self.context["migration_status"]
            == ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value
        )


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
