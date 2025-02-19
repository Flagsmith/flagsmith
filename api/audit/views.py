from abc import abstractmethod
from datetime import timedelta

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
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
from organisations.models import Organisation, OrganisationRole


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=AuditLogsQueryParamSerializer()),
)
class _BaseAuditLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet  # type: ignore[type-arg]
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

        queryset = AuditLog.objects.filter(q).select_related(
            "project", "environment", "author"
        )

        return self._apply_visibility_limits(queryset)

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        return {"retrieve": AuditLogRetrieveSerializer}.get(
            self.action, AuditLogListSerializer
        )

    def _get_base_filters(self) -> Q:  # pragma: no cover
        return Q()

    def _apply_visibility_limits(
        self, queryset: QuerySet[AuditLog]
    ) -> QuerySet[AuditLog]:
        organisation = self._get_organisation()
        if not organisation:
            return AuditLog.objects.none()  # type: ignore[no-any-return]

        subscription_metadata = organisation.subscription.get_subscription_metadata()
        if (
            subscription_metadata
            and (limit := subscription_metadata.audit_log_visibility_days) is not None
        ):
            queryset = queryset.filter(
                created_date__gte=timezone.now() - timedelta(days=limit)
            )

        return queryset

    @abstractmethod
    def _get_organisation(self) -> Organisation | None:
        raise NotImplementedError("Must implement _get_organisation()")


class AllAuditLogViewSet(_BaseAuditLogViewSet):
    def _get_base_filters(self) -> Q:
        return Q(
            project__organisation__userorganisation__user=self.request.user,
            project__organisation__userorganisation__role=OrganisationRole.ADMIN,
        )

    def _get_organisation(self) -> Organisation | None:
        """
        This is a bit of a hack but since this endpoint is no longer used (by the UI
        at least) we just return the first organisation the user has (most users only
        have a single organisation anyway).

        Since this function is only used here for limiting access (by number of days)
        to the audit log, the blast radius here is pretty small.

        Since we're applying the base filters to the query set
        """
        return (
            self.request.user.organisations.filter(  # type: ignore[union-attr]
                userorganisation__role=OrganisationRole.ADMIN
            )
            .select_related("subscription", "subscription_information_cache")
            .first()
        )


class OrganisationAuditLogViewSet(_BaseAuditLogViewSet):
    permission_classes = [IsAuthenticated, OrganisationAuditLogPermissions]

    def _get_base_filters(self) -> Q:
        return Q(project__organisation__id=self.kwargs["organisation_pk"])

    def _get_organisation(self) -> Organisation | None:
        return (  # type: ignore[no-any-return]
            Organisation.objects.select_related(
                "subscription", "subscription_information_cache"
            )
            .filter(pk=self.kwargs["organisation_pk"])
            .first()
        )


class ProjectAuditLogViewSet(_BaseAuditLogViewSet):
    permission_classes = [IsAuthenticated, ProjectAuditLogPermissions]

    def _get_base_filters(self) -> Q:
        return Q(project__id=self.kwargs["project_pk"])

    def _get_organisation(self) -> Organisation | None:
        return (  # type: ignore[no-any-return]
            Organisation.objects.select_related(
                "subscription", "subscription_information_cache"
            )
            .filter(projects__pk=self.kwargs["project_pk"])
            .first()
        )
