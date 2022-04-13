from rest_framework import viewsets
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT


class IntegrationCommonViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None  # set here to ensure documentation is correct
    model_class = None

    def get_queryset(self):
        environment_api_key = self.kwargs["environment_api_key"]

        if environment := Environment.objects.filter(
            api_key=environment_api_key
        ).first():
            if not self.request.user.has_environment_permission(
                VIEW_ENVIRONMENT, environment
            ):
                raise PermissionDenied(
                    "User does not have permission to perform action in environment."
                )

            return self.model_class.objects.filter(environment=environment)

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
