from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from environments.models import Environment


class IntegrationCommonViewSet(viewsets.ModelViewSet):
    serializer_class = None
    pagination_class = None  # set here to ensure documentation is correct
    model_class = None

    def get_queryset(self):
        environment_api_key = self.kwargs["environment_api_key"]
        environment = get_object_or_404(
            self.request.user.get_permitted_environments(["VIEW_ENVIRONMENT"]),
            api_key=environment_api_key,
        )

        return self.model_class.objects.filter(environment=environment)

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
