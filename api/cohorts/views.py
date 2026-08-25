from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from api.serializers import ErrorSerializer
from cohorts import services
from cohorts.models import Cohort, CohortSyncKey
from cohorts.permissions import CohortPermission, CohortPlanPermission
from cohorts.serializers import (
    CohortCsvSyncResultSerializer,
    CohortCsvSyncSerializer,
    CohortSerializer,
    CohortSyncKeySerializer,
)
from environments.models import Environment
from environments.views import NestedEnvironmentViewSet


@extend_schema_view(
    list=extend_schema(description="List the environment's cohorts."),
    create=extend_schema(
        description="Create a cohort and the managed segment that targets it."
    ),
    retrieve=extend_schema(description="Retrieve a cohort."),
    destroy=extend_schema(
        description=(
            "Request cohort deletion. Memberships are drained from identity "
            "data first; the cohort and its segment are deleted once drained."
        ),
        responses={202: None},
    ),
)
class CohortViewSet(
    NestedEnvironmentViewSet[Cohort],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = CohortSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CohortPlanPermission, CohortPermission]
    model_class = Cohort
    lookup_field = "id"
    lookup_url_kwarg = "cohort_id"

    def get_queryset(self) -> QuerySet[Cohort]:
        # A cohort awaiting drain-then-delete is already gone from the
        # user's point of view.
        return (
            super()
            .get_queryset()
            .filter(deletion_requested_at__isnull=True)
            .select_related("segment")
            .order_by("id")
        )

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        services.delete_cohort(self.get_object())
        return Response(status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        description=(
            "Replace the cohort's members with the identifiers found in the "
            "uploaded CSV file and trigger a sync to identity data. "
            "`identifier_column` is the 0-based index of the column holding "
            "the identifiers; `has_header` skips the first row when true."
        ),
        request=CohortCsvSyncSerializer,
        responses={
            202: CohortCsvSyncResultSerializer,
            400: ErrorSerializer,
            413: ErrorSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="sync-csv",
        parser_classes=[MultiPartParser],
    )
    def sync_csv(self, request: Request, *args: object, **kwargs: object) -> Response:
        cohort = self.get_object()
        serializer = CohortCsvSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.sync_cohort_memberships_from_csv(
            cohort=cohort, **serializer.validated_data
        )
        return Response(
            CohortCsvSyncResultSerializer(result).data,
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema_view(
    create=extend_schema(
        description=(
            "Create a cohort sync key. The response is the only time the "
            "plaintext key is available."
        )
    ),
    destroy=extend_schema(description="Revoke a cohort sync key."),
)
class CohortSyncKeyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet[CohortSyncKey],
):
    serializer_class = CohortSyncKeySerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CohortPlanPermission, CohortPermission]
    lookup_field = "prefix"

    def get_queryset(self) -> QuerySet[CohortSyncKey]:
        return CohortSyncKey.objects.filter(
            environment__api_key=self.kwargs.get("environment_api_key"),
            revoked=False,
        ).order_by("-created")

    def perform_create(self, serializer: BaseSerializer[CohortSyncKey]) -> None:
        environment = Environment.objects.get(
            api_key=self.kwargs.get("environment_api_key")
        )
        serializer.save(environment=environment, created_by=self.request.user)

    def perform_destroy(self, instance: CohortSyncKey) -> None:
        instance.revoked = True
        instance.save(update_fields=["revoked"])
