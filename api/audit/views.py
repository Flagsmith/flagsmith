from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from app.pagination import CustomPagination
from audit.models import AuditLog
from audit.permissions import AuditLogPermissions
from audit.serializers import AuditLogSerializer, AuditLogsQueryParamSerializer


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=AuditLogsQueryParamSerializer()),
)
class _BaseAuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer
    pagination_class = CustomPagination
    filterset_fields = ["is_system_event"]

    def get_queryset(self):
        q = self._get_base_filters()

        serializer = AuditLogsQueryParamSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)
        project_id = serializer.data.get("project")
        environment_ids = serializer.data.get("environments")

        if project_id:
            q = q & Q(project__id=project_id)
        if environment_ids:
            q = q & Q(environment__id__in=environment_ids)

        search = serializer.data.get("search")
        if search:
            q = q & Q(log__icontains=search)

        return AuditLog.objects.filter(q).select_related(
            "project", "environment", "author"
        )

    def _get_base_filters(self) -> Q:
        return Q()


class AllAuditLogViewSet(_BaseAuditLogViewSet):
    def _get_base_filters(self) -> Q:
        return Q(project__organisation__users=self.request.user)


class OrganisationAuditLogViewSet(_BaseAuditLogViewSet):
    permission_classes = [IsAuthenticated, AuditLogPermissions]

    def _get_base_filters(self) -> Q:
        return Q(project__organisation__id=self.kwargs["organisation_pk"])
