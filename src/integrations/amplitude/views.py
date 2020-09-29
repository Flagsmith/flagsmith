from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from integrations.amplitude.models import AmplitudeConfiguration
from integrations.amplitude.serializers import AmplitudeConfigurationSerializer

project_query_param = openapi.Parameter('project', openapi.IN_QUERY, description='ID of the project to filter on',
                                        type=openapi.TYPE_INTEGER)


# @method_decorator(name='list', decorator=swagger_auto_schema(manual_parameters=[project_query_param]))
class AmplitudeConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = AmplitudeConfigurationSerializer

    def get_queryset(self):
        q = Q(project__organisation__in=self.request.user.organisations.all())
        if 'project' in self.request.query_params:
            project_id = self._get_value_as_int(self.request.query_params.get('project'))
            q = q & Q(project__id=project_id)
            return AmplitudeConfiguration.objects.filter(q)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)

