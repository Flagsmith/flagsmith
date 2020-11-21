import coreapi
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer

project_query_param = openapi.Parameter(
    "project",
    openapi.IN_QUERY,
    description="ID of the project to filter on",
    type=openapi.TYPE_INTEGER,
)
environment_query_param = openapi.Parameter(
    "environment",
    openapi.IN_QUERY,
    description="ID of the environment to filter on "
    "(Note `id` required, not `api_key`)",
    type=openapi.TYPE_INTEGER,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[project_query_param, environment_query_param]
    ),
)
class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        q = Q(project__organisation__in=self.request.user.organisations.all())
        if "project" in self.request.query_params:
            project_id = self._get_value_as_int(
                self.request.query_params.get("project")
            )
            q = q & Q(project__id=project_id)
        if "environment" in self.request.query_params:
            environment_id = self._get_value_as_int(
                self.request.query_params.get("environment")
            )
            q = q & (Q(environment__id=environment_id) | Q(environment=None))
        return AuditLog.objects.filter(q)

    def _get_value_as_int(self, value):
        try:
            return int(value)
        except ValueError:
            return None
