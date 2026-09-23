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
    CreateUpdateUserEnvironmentPermissionSerializer,
    CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer,
    ListUserEnvironmentPermissionSerializer,
    ListUserPermissionGroupEnvironmentPermissionSerializer,
)


class UserEnvironmentPermissionsViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return UserEnvironmentPermission.objects.none()

        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return UserEnvironmentPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "list":
            return ListUserEnvironmentPermissionSerializer

        return CreateUpdateUserEnvironmentPermissionSerializer

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)


class UserPermissionGroupEnvironmentPermissionsViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return UserPermissionGroupEnvironmentPermission.objects.none()

        if not self.kwargs.get("environment_api_key"):
            raise ValidationError("Missing environment key.")

        return UserPermissionGroupEnvironmentPermission.objects.filter(
            environment__api_key=self.kwargs["environment_api_key"]
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "list":
            return ListUserPermissionGroupEnvironmentPermissionSerializer

        return CreateUpdateUserPermissionGroupEnvironmentPermissionSerializer

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        serializer.save(environment=environment)
