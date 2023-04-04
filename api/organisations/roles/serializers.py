from rest_framework import serializers

from .models import (
    GroupRole,
    Role,
    RoleEnvironmentPermission,
    RoleOrganisationPermission,
    RoleProjectPermission,
    UserRole,
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "organisation")
        read_only_fields = ("organisation",)


class RoleEnvironmentPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleEnvironmentPermission
        fields = ("id", "role", "environment", "permissions", "admin")


class RoleProjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleProjectPermission
        fields = ("id", "role", "project", "permissions", "admin")


class RoleOrganisationPermisssionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleOrganisationPermission
        fields = (
            "id",
            "role",
            "organisation",
            "permissions",
        )
        read_only_fields = ("organisation",)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("id", "user", "role")


class GroupRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRole
        fields = ("id", "group", "role")
