from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

from integrations.datadog.models import DataDogConfiguration
from integrations.datadog.serializers import DataDogConfigurationSerializer

project_query_param = openapi.Parameter('project', openapi.IN_QUERY, description='ID of the project to filter on',
                                        type=openapi.TYPE_INTEGER)

@method_decorator(name='list', decorator=swagger_auto_schema(manual_parameters=[project_query_param]))
class DataDogConfigurationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DataDogConfigurationSerializer

    def get_queryset(self):
        q = Q(project__organisation__in=self.request.user.organisations.all())
        if 'project' in self.request.query_params:
            project_id = self._get_value_as_int(self.request.query_params.get('project'))
            q = q & Q(project__id=project_id)
            return DataDogConfiguration.objects.filter(q)

    def _get_value_as_int(self, value):
        try:
            return int(value)
        except ValueError:
            return None
