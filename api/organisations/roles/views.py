from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
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
        return Role.objects.filter(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer):
        organisation_id = int(self.kwargs["organisation_pk"])
        serializer.save(organisation_id=organisation_id)

    def perform_create(self, serializer):
        organisation_id = int(self.kwargs["organisation_pk"])
        serializer.save(organisation_id=organisation_id)


class UserRoleViewSet(viewsets.ModelViewSet):
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
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
        return GroupRole.objects.filter(role_id=self.kwargs["role_pk"])

    def perform_update(self, serializer):
        role_id = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_id)

    def perform_create(self, serializer):
        role_id = int(self.kwargs.get("role_pk"))
        serializer.save(role_id=role_id)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "environment",
                openapi.IN_QUERY,
                "ID of the environment to filter by.",
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ]
    ),
)
class RoleEnvironmentPermissionsViewSet(viewsets.ModelViewSet):
    serializer_class = RoleEnvironmentPermissionSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        q = Q()
        if self.action == "list":
            environment_id = self.request.query_params.get("environment")
            if not environment_id:
                raise ValidationError("'environment' GET parameter is required.")
            q &= Q(environment__id=environment_id)

        return RoleEnvironmentPermission.objects.filter(q)

    def perform_create(self, serializer):
        role_pk = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_pk)

    def perform_update(self, serializer):
        role_pk = int(self.kwargs["role_pk"])
        serializer.save(role_id=role_pk)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "project",
                openapi.IN_QUERY,
                "ID of the project to filter by.",
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ]
    ),
)
class RoleProjectPermissionsViewSet(viewsets.ModelViewSet):
    serializer_class = RoleProjectPermissionSerializer
    permission_classes = [IsAuthenticated, NestedRolePermission]

    def get_queryset(self):
        q = Q()
        if self.action == "list":
            project_id = self.request.query_params.get("project")
            if not project_id:
                raise ValidationError("'project' GET parameter is required.")
            q &= Q(project__id=project_id)

        return RoleProjectPermission.objects.filter(q)

    def perform_create(self, serializer):
        role = Role.objects.get(id=self.kwargs["role_pk"])
        serializer.save(role=role)
