from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from organisations.roles.models import (
    GroupRole,
    Role,
    RoleEnvironmentPermission,
    RoleProjectPermission,
    UserRole,
)

from .permissions import NestedRolePermission
from .serializers import (
    GroupRoleSerializer,
    RoleEnvironmentPermissionSerializer,
    RoleProjectPermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
)


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self):
        if "organisation_pk" not in self.kwargs:
            raise ValidationError("Missing required path parameter 'organisation_pk'")

        return Role.objects.filter(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer):
        organisation_id = int(self.kwargs["organisation_pk"])
        serializer.save(organisation_id=organisation_id)

    def perform_create(self, serializer):
        organisation_id = int(self.kwargs["organisation_pk"])
        serializer.save(organisation_id=organisation_id)


class RoleEnvironmentPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = RoleEnvironmentPermissionSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return RoleEnvironmentPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def perform_create(self, serializer):
        role_pk = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_pk)

    def perform_update(self, serializer):
        role_pk = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_pk)


class RoleProjectPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = RoleProjectPermissionSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return RoleProjectPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def perform_create(self, serializer):
        role = Role.objects.get(id=self.kwargs["role_pk"])
        serializer.save(role=role)


class UserRoleViewSet(viewsets.ModelViewSet):
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        if "role_pk" not in self.kwargs:
            raise ValidationError("Missing required path parameter 'role_pk'")
        return UserRole.objects.filter(role_id=self.kwargs["role_pk"])

    def perform_update(self, serializer):
        role_id = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_id)

    def perform_create(self, serializer):
        role_id = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_id)


class GroupRoleViewSet(viewsets.ModelViewSet):
    serializer_class = GroupRoleSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        if "role_pk" not in self.kwargs:
            raise ValidationError("Missing required path parameter 'role_pk'")
        return GroupRole.objects.filter(role_id=self.kwargs["role_pk"])

    def perform_update(self, serializer):
        role_id = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_id)

    def perform_create(self, serializer):
        role_id = int(self.kwargs.get("role_pk"))
        serializer.save(role_id=role_id)
