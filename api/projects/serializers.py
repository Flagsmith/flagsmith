from django.conf import settings
from rest_framework import serializers

from environments.dynamodb.migrator import IdentityMigrator
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
    is_identity_migration_done = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "organisation",
            "hide_disabled_flags",
            "enable_dynamo_db",
            "is_identity_migration_done",
        )

    def get_is_identity_migration_done(self, obj: Project) -> bool:
        if settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            identity_migrator = IdentityMigrator(obj.id)
            return identity_migrator.is_migration_done
        return False


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
