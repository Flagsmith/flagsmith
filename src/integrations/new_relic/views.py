from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from integrations.new_relic.models import NewRelicConfiguration
from integrations.new_relic.serializers import NewRelicConfigurationSerializer


class NewRelicConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = NewRelicConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct

    def get_queryset(self):
        project = get_object_or_404(
            self.request.user.get_permitted_projects(["VIEW_PROJECT"]),
            pk=self.kwargs["project_pk"],
        )
        return NewRelicConfiguration.objects.filter(project=project)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_pk"]
        if NewRelicConfiguration.objects.filter(project_id=project_id).exists():
            raise ValidationError(
                "NewRelicConfiguration for this project already exist."
            )

        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)
