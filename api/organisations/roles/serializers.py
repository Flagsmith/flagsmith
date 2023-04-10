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
        read_only_fields = ("role",)

    def validate(self, data):
        organisation_pk = int(self.context["view"].kwargs["organisation_pk"])
        if data["environment"].project.organisation_id != organisation_pk:
            raise serializers.ValidationError(
                {"environment": "Environment does not belong to this organisation"}
            )
        return data


class RoleProjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleProjectPermission
        fields = ("id", "role", "project", "permissions", "admin")
        read_only_fields = ("role",)

    def validate(self, data):
        organisation_pk = int(self.context["view"].kwargs["organisation_pk"])
        if data["project"].organisation_id != organisation_pk:
            raise serializers.ValidationError(
                {"project": "Project does not belong to this organisation"}
            )
        return data


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
        read_only_fields = ("role",)

    def validate(self, data):
        organisation_pk = int(self.context["view"].kwargs["organisation_pk"])

        if not data["user"].belongs_to(organisation_pk):
            raise serializers.ValidationError(
                {"user": "User does not belong to this organisation"}
            )
        return data


class GroupRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRole
        fields = ("id", "group", "role")
        read_only_fields = ("role",)

    def validate(self, data):
        organisation_pk = int(self.context["view"].kwargs["organisation_pk"])
        if not data["group"].organisation_id == organisation_pk:
            raise serializers.ValidationError(
                {"group": "Group does not belong to this organisation"}
            )
        return data
