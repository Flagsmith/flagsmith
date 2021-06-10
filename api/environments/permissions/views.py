from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from environments.models import Environment
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from environments.permissions.permissions import NestedEnvironmentPermissions
from environments.permissions.serializers import (
    ListUserEnvironmentPermissionSerializer,
    CreateUpdateUserEnvironmentPermissionSerializer,
    ListUserPermissionGroupEnvironmentPermissionSerializer,
    CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer,
)


class UserEnvironmentPermissionsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    def get_queryset(self):
        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return UserEnvironmentPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserEnvironmentPermissionSerializer

        return CreateUpdateUserEnvironmentPermissionSerializer

    def perform_create(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)


class UserPermissionGroupEnvironmentPermissionsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    def get_queryset(self):
        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return UserPermissionGroupEnvironmentPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserPermissionGroupEnvironmentPermissionSerializer

        return CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer

    def perform_create(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)
