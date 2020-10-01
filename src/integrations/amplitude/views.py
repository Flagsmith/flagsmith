from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from integrations.amplitude.serializers import AmplitudeConfigurationSerializer
from .models import AmplitudeConfiguration


class AmplitudeConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = AmplitudeConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct

    def get_queryset(self):
        environment_api_key = self.kwargs['environment_api_key']
        environment = get_object_or_404(self.request.user.get_permitted_environments(['VIEW_ENVIRONMENT']),
                                        api_key=environment_api_key)

        return AmplitudeConfiguration.objects.filter(environment)

    def perform_create(self, serializer):
        environment = self.get_environment_from_request()
        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = self.get_environment_from_request()
        serializer.save(environment=environment)
