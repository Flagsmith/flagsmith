from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from permissions.serializers import CreateUpdateUserPermissionSerializerABC
from users.serializers import UserListSerializer, UserPermissionGroupSerializerDetail


class CreateUpdateUserEnvironmentPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserEnvironmentPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("user",)


class ListUserEnvironmentPermissionSerializer(
    CreateUpdateUserEnvironmentPermissionSerializer
):
    user = UserListSerializer()


class CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer(
    CreateUpdateUserPermissionSerializerABC
):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserPermissionGroupEnvironmentPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ("group",)


class ListUserPermissionGroupEnvironmentPermissionSerializer(
    CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer
):
    group = UserPermissionGroupSerializerDetail()
