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
        fields = ("name", "organisation")


class RoleEnvironmentPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleEnvironmentPermission
        fields = ("role", "environment", "permissions", "admin")


class RoleProjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleProjectPermission
        fields = ("role", "project", "permissions", "admin")


class RoleOrganisationPermisssionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleOrganisationPermission
        fields = (
            "role",
            "organisation",
            "permissions",
        )
        read_only_fields = ("organisation",)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("user", "role")


class GroupRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRole
        fields = ("group", "role")
