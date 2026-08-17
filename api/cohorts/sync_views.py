import typing
import uuid as uuid_module

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from cohorts import services
from cohorts.authentication import CohortSyncKeyAuthentication
from cohorts.models import Cohort, CohortSourceType, CohortSyncKey
from cohorts.permissions import HasCohortSyncKey
from cohorts.serializers import (
    AmplitudeListSerializer,
    CohortSyncMembersSerializer,
)
from projects.exceptions import DynamoNotEnabledError

_LIST_RESPONSE = inline_serializer(
    "AmplitudeListResponse", {"list_id": serializers.UUIDField()}
)


@extend_schema_view(
    create=extend_schema(
        description=(
            "Called by Amplitude once per cohort sync setup; creates the "
            "backing cohort and returns its identifier as the list ID."
        ),
        request=AmplitudeListSerializer,
        responses={200: _LIST_RESPONSE},
    ),
    add=extend_schema(request=CohortSyncMembersSerializer, responses={200: None}),
    remove=extend_schema(request=CohortSyncMembersSerializer, responses={200: None}),
)
class AmplitudeCohortSyncViewSet(viewsets.ViewSet):
    authentication_classes = [CohortSyncKeyAuthentication]
    permission_classes = [HasCohortSyncKey]

    def create(self, request: Request) -> Response:
        serializer = AmplitudeListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        environment = self._get_key(request).environment
        if not services.edge_sync_enabled(environment.project):
            raise DynamoNotEnabledError()
        cohort = services.create_cohort_for_source(
            environment=environment,
            name=serializer.validated_data["name"],
            source_type=CohortSourceType.AMPLITUDE,
        )
        return Response({"list_id": str(cohort.uuid)})

    @action(detail=True, methods=["POST"])
    def add(self, request: Request, pk: str) -> Response:
        cohort = self._get_cohort(request, pk)
        serializer = CohortSyncMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_cohort_members(cohort, serializer.validated_data["user_ids"])
        return Response()

    @action(detail=True, methods=["POST"])
    def remove(self, request: Request, pk: str) -> Response:
        cohort = self._get_cohort(request, pk)
        serializer = CohortSyncMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.remove_cohort_members(cohort, serializer.validated_data["user_ids"])
        return Response()

    def _get_key(self, request: Request) -> CohortSyncKey:
        # HasCohortSyncKey has already established the type.
        return typing.cast(CohortSyncKey, request.auth)

    def _get_cohort(self, request: Request, pk: str) -> Cohort:
        try:
            list_uuid = uuid_module.UUID(pk)
        except ValueError:
            raise NotFound("List not found.")
        cohort: Cohort | None = Cohort.objects.filter(
            uuid=list_uuid,
            environment=self._get_key(request).environment,
            source_type=CohortSourceType.AMPLITUDE,
            deletion_requested_at__isnull=True,
        ).first()
        if cohort is None:
            raise NotFound("List not found.")
        return cohort
