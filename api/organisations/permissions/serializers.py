from rest_framework import serializers

from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from users.serializers import UserListSerializer, UserPermissionGroupSerializer


class UserOrganisationPermissionUpdateCreateSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = UserOrganisationPermission
        fields = ("id", "user", "permissions")


class UserOrganisationPermissionListSerializer(
    UserOrganisationPermissionUpdateCreateSerializer
):
    user = UserListSerializer()


class UserPermissionGroupOrganisationPermissionUpdateCreateSerializer(
    serializers.ModelSerializer  # type: ignore[type-arg]
):
    class Meta:
        model = UserPermissionGroupOrganisationPermission
        fields = ("id", "group", "permissions")


class UserPermissionGroupOrganisationPermissionListSerializer(
    UserPermissionGroupOrganisationPermissionUpdateCreateSerializer
):
    group = UserPermissionGroupSerializer()
