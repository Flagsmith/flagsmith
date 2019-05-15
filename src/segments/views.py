from rest_framework import viewsets

from projects.models import Project
from . import serializers


class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SegmentSerializer

    def get_queryset(self):
        project = Project.objects.get(pk=self.kwargs['project_pk'])
        return project.segments.all()
