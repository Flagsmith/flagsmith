from rest_framework import serializers

from permissions.serializers import CreateUpdateUserPermissionSerializerABC
from projects.models import Project, UserProjectPermission, UserPermissionGroupProjectPermission
from users.serializers import UserListSerializer, UserPermissionGroupSerializerList


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'organisation', 'hide_disabled_flags')


class CreateUpdateUserProjectPermissionSerializer(CreateUpdateUserPermissionSerializerABC):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ('user',)


class ListUserProjectPermissionSerializer(CreateUpdateUserProjectPermissionSerializer):
    user = UserListSerializer()


class CreateUpdateUserPermissionGroupProjectPermissionSerializer(CreateUpdateUserPermissionSerializerABC):
    class Meta(CreateUpdateUserPermissionSerializerABC.Meta):
        model = UserPermissionGroupProjectPermission
        fields = CreateUpdateUserPermissionSerializerABC.Meta.fields + ('group',)


class ListUserPermissionGroupProjectPermissionSerializer(CreateUpdateUserPermissionGroupProjectPermissionSerializer):
    group = UserPermissionGroupSerializerList()
