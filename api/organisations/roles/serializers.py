from rest_framework import serializers

from .models import (
    GroupRole,
    Role,
    RoleEnvironmentPermission,
    RoleProjectPermission,
    UserRole,
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("name", "organisation", "permissions")


class RoleEnvironmentPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleEnvironmentPermission
        fields = ("role", "environment", "permissions", "admin")


class RoleProjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleProjectPermission
        fields = ("role", "project", "permissions", "admin")


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("user", "role")


class GroupRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRole
        fields = ("group", "role")
