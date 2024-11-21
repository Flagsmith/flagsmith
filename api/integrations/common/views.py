from common.environments.permissions import VIEW_ENVIRONMENT
from common.projects.permissions import VIEW_PROJECT
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from environments.models import Environment
from environments.permissions.permissions import NestedEnvironmentPermissions
from organisations.permissions.permissions import (
    NestedOrganisationEntityPermission,
)
from projects.permissions import NestedProjectPermissions


class EnvironmentIntegrationCommonViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None  # set here to ensure documentation is correct
    model_class = None

    def initial(self, request: Request, *args, **kwargs) -> None:
        super().initial(request, *args, **kwargs)
        request.environment = get_object_or_404(
            Environment,
            api_key=self.kwargs["environment_api_key"],
        )

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        return self.model_class.objects.filter(environment=self.request.environment)

    def get_permissions(self) -> list[BasePermission]:
        return [
            IsAuthenticated(),
            NestedEnvironmentPermissions(
                action_permission_map={"retrieve": VIEW_ENVIRONMENT},
            ),
        ]

    def perform_create(self, serializer: BaseSerializer) -> None:
        if self.get_queryset().exists():
            raise ValidationError(
                "This integration already exists for this environment."
            )
        serializer.save(environment=self.request.environment)

    def perform_update(self, serializer: BaseSerializer) -> None:
        serializer.save(environment=self.request.environment)


class ProjectIntegrationBaseViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None
    model_class = None

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        return self.model_class.objects.filter(project_id=self.kwargs["project_pk"])

    def get_permissions(self) -> list[BasePermission]:
        return [
            NestedProjectPermissions(
                action_permission_map={"retrieve": VIEW_PROJECT},
            ),
        ]

    def perform_create(self, serializer: BaseSerializer) -> None:
        if self.get_queryset().exists():
            raise ValidationError("This integration already exists for this project.")
        serializer.save(project_id=self.kwargs["project_pk"])

    def perform_update(self, serializer: BaseSerializer) -> None:
        serializer.save(project_id=self.kwargs["project_pk"])


class OrganisationIntegrationBaseViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None
    model_class = None

    permission_classes = [IsAuthenticated, NestedOrganisationEntityPermission]

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        return self.model_class.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        )

    def perform_create(self, serializer: BaseSerializer) -> None:
        if self.get_queryset().exists():
            raise ValidationError(
                "This integration already exists for this organisation."
            )
        serializer.save(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer: BaseSerializer) -> None:
        serializer.save(organisation_id=self.kwargs["organisation_pk"])
