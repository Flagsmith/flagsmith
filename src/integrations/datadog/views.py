from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from integrations.datadog.models import DataDogConfiguration
from integrations.datadog.serializers import DataDogConfigurationSerializer


class DataDogConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = DataDogConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct

    def get_queryset(self):
        project = get_object_or_404(
            self.request.user.get_permitted_projects(["VIEW_PROJECT"]),
            pk=self.kwargs["project_pk"],
        )
        return DataDogConfiguration.objects.filter(project=project)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_pk"]
        if DataDogConfiguration.objects.filter(project_id=project_id).exists():
            raise ValidationError(
                "DataDogConfiguration for this project already exist."
            )

        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)
