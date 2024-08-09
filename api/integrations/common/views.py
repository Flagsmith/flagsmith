from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT
from projects.permissions import VIEW_PROJECT


class EnvironmentIntegrationCommonViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None  # set here to ensure documentation is correct
    model_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        environment_api_key = self.kwargs["environment_api_key"]

        try:
            environment = Environment.objects.get(api_key=environment_api_key)
            if not self.request.user.has_environment_permission(
                VIEW_ENVIRONMENT, environment
            ):
                raise PermissionDenied(
                    "User does not have permission to perform action in environment."
                )

            return self.model_class.objects.filter(environment=environment)
        except Environment.DoesNotExist:
            raise NotFound("Environment not found.")

    def perform_create(self, serializer):
        environment = self.get_environment_from_request()

        if self.model_class.objects.filter(environment=environment).exists():
            raise ValidationError(
                f"{self.model_class.__name__} for environment already exist."
            )

        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = self.get_environment_from_request()
        serializer.save(environment=environment)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs["environment_api_key"])


class ProjectIntegrationBaseViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None
    model_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        project = get_object_or_404(
            self.request.user.get_permitted_projects(VIEW_PROJECT),
            pk=self.kwargs["project_pk"],
        )
        return self.model_class.objects.filter(project=project)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_pk"]
        if self.model_class.objects.filter(project_id=project_id).exists():
            raise ValidationError(
                f"{self.model_class.__name__} for this project already exists."
            )
        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)


class OrganisationIntegrationBaseViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None
    model_class = None

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        if self.request.user.is_organisation_admin(
            organisation_id := self.kwargs["organisation_pk"]
        ):
            return self.model_class.filter(organisation_id=organisation_id)

        raise Http404()

    def perform_create(self, serializer) -> None:
        organisation_id = self.kwargs["organisation_pk"]
        if self.model_class.objects.filter(organisation_id=organisation_id).exists():
            raise ValidationError(
                f"{self.model_class.__name__} for this organisation already exists."
            )
        serializer.save(organisation_id=organisation_id)

    def perform_update(self, serializer) -> None:
        organisation_id = self.kwargs["organisation_pk"]
        serializer.save(organisation_id=organisation_id)
