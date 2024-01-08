from django.db.models import Q, QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from app.pagination import CustomPagination
from audit.models import AuditLog
from audit.permissions import (
    OrganisationAuditLogPermissions,
    ProjectAuditLogPermissions,
)
from audit.serializers import (
    AuditLogListSerializer,
    AuditLogRetrieveSerializer,
    AuditLogsQueryParamSerializer,
)
from organisations.models import OrganisationRole


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=AuditLogsQueryParamSerializer()),
)
class _BaseAuditLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet[AuditLog]:
        q = self._get_base_filters()

        serializer = AuditLogsQueryParamSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        if project_id := serializer.data.get("project"):
            q = q & Q(project__id=project_id)
        if environment_ids := serializer.data.get("environments"):
            q = q & Q(environment__id__in=environment_ids)
        if is_system_event := serializer.data.get("is_system_event") is not None:
            q = q & Q(is_system_event=is_system_event)

        search = serializer.data.get("search")
        if search:
            q = q & Q(log__icontains=search)

        return AuditLog.objects.filter(q).select_related(
            "project", "environment", "author"
        )

    def _get_base_filters(self) -> Q:
        return Q()

    def get_serializer_class(self):
        return {"retrieve": AuditLogRetrieveSerializer}.get(
            self.action, AuditLogListSerializer
        )


class AllAuditLogViewSet(_BaseAuditLogViewSet):
    def _get_base_filters(self) -> Q:
        return Q(
            project__organisation__userorganisation__user=self.request.user,
            project__organisation__userorganisation__role=OrganisationRole.ADMIN,
        )


class OrganisationAuditLogViewSet(_BaseAuditLogViewSet):
    permission_classes = [IsAuthenticated, OrganisationAuditLogPermissions]

    def _get_base_filters(self) -> Q:
        return Q(project__organisation__id=self.kwargs["organisation_pk"])


class ProjectAuditLogViewSet(_BaseAuditLogViewSet):
    permission_classes = [IsAuthenticated, ProjectAuditLogPermissions]

    def _get_base_filters(self) -> Q:
        return Q(project__id=self.kwargs["project_pk"])
