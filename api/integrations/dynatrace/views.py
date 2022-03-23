from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from integrations.dynatrace.models import DynatraceConfiguration
from integrations.dynatrace.serializers import DynatraceConfigurationSerializer


class DynatraceConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = DynatraceConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct

    def get_queryset(self):
        project = get_object_or_404(
            self.request.user.get_permitted_projects(["VIEW_PROJECT"]),
            pk=self.kwargs["project_pk"],
        )
        return DynatraceConfiguration.objects.filter(project=project)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_pk"]
        if DynatraceConfiguration.objects.filter(project_id=project_id).exists():
            raise ValidationError(
                "DynatraceConfiguration for this project already exist."
            )

        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)
