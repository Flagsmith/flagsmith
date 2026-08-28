import json
import typing

import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cohorts import services
from cohorts.authentication import CohortSyncKeyAuthentication
from cohorts.models import Cohort, CohortSourceType, CohortSyncKey
from cohorts.permissions import CohortSyncPlanPermission, HasCohortSyncKey
from cohorts.serializers import (
    AmplitudeListSerializer,
    CohortSyncMembersSerializer,
    MixpanelWebhookSerializer,
    WebhookSyncMembersSerializer,
)

_LIST_RESPONSE = inline_serializer(
    "AmplitudeListResponse", {"list_id": serializers.UUIDField()}
)

_MIXPANEL_RESPONSE = inline_serializer(
    "MixpanelWebhookResponse",
    {"action": serializers.CharField(), "status": serializers.CharField()},
)

_MIXPANEL_FAILURE_RESPONSE = inline_serializer(
    "MixpanelWebhookFailureResponse",
    {
        "action": serializers.CharField(allow_null=True),
        "status": serializers.CharField(),
        "error": inline_serializer(
            "MixpanelWebhookError",
            {
                "message": serializers.CharField(),
                "code": serializers.IntegerField(),
            },
        ),
    },
)

logger = structlog.get_logger("cohorts")


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
    permission_classes = [HasCohortSyncKey, CohortSyncPlanPermission]

    def create(self, request: Request) -> Response:
        serializer = AmplitudeListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        environment = self._get_key(request).environment
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
        cohort = services.get_active_cohort(
            environment=self._get_key(request).environment,
            source_type=CohortSourceType.AMPLITUDE,
            uuid=pk,
        )
        if cohort is None:
            raise NotFound("List not found.")
        return cohort


class MixpanelCohortSyncView(APIView):
    """
    The receiving end of Mixpanel's Custom Webhook cohort destination:
    https://docs.mixpanel.com/docs/cohort-sync/webhooks

    Mixpanel POSTs every message to this one URL and reads the outcome from
    the response body, which must repeat the action alongside a
    success/failure status.
    """

    authentication_classes = [CohortSyncKeyAuthentication]
    permission_classes = [HasCohortSyncKey, CohortSyncPlanPermission]

    @extend_schema(
        description=(
            "Called by Mixpanel every sync cycle with the cohort's full "
            "membership (`members`) or the changes since the last sync "
            "(`add_members`/`remove_members`)."
        ),
        request=MixpanelWebhookSerializer,
        responses={
            200: _MIXPANEL_RESPONSE,
            400: _MIXPANEL_FAILURE_RESPONSE,
            404: _MIXPANEL_FAILURE_RESPONSE,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = MixpanelWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return self._failure(
                request,
                message=(
                    f"Invalid payload: {json.dumps(serializer.errors, default=str)}"
                ),
                code=400,
            )

        data = serializer.validated_data
        webhook_action: str = data["action"]
        parameters = data["parameters"]
        identifiers = [
            member["mixpanel_distinct_id"] for member in parameters["members"]
        ]
        environment = typing.cast(CohortSyncKey, request.auth).environment

        if webhook_action == "members":
            if services.cohort_deletion_in_progress(
                environment=environment,
                source_type=CohortSourceType.MIXPANEL,
                external_id=parameters["mixpanel_cohort_id"],
            ):
                # Recreating the cohort while its memberships are still being
                # drained would resurrect it. The 404 pauses the sync and
                # emails the customer.
                return self._failure(
                    request, message="Cohort is being deleted.", code=404
                )
            # A large first sync arrives as several requests, each one page
            # of members. Every page only adds; removals can't be detected
            # without seeing all pages at once.
            cohort = services.get_cohort_for_source(
                environment=environment,
                source_type=CohortSourceType.MIXPANEL,
                external_id=parameters["mixpanel_cohort_id"],
            ) or services.create_cohort_for_source(
                environment=environment,
                name=parameters["mixpanel_cohort_name"],
                source_type=CohortSourceType.MIXPANEL,
                external_id=parameters["mixpanel_cohort_id"],
            )
            services.add_cohort_members(cohort, identifiers)
        else:
            cohort_or_none = services.get_cohort_for_source(
                environment=environment,
                source_type=CohortSourceType.MIXPANEL,
                external_id=parameters["mixpanel_cohort_id"],
            )
            if cohort_or_none is None:
                # A 404 makes Mixpanel pause the sync and email the customer,
                # which is what should happen when the cohort was deleted in
                # Flagsmith but Mixpanel is still syncing it.
                return self._failure(request, message="Cohort not found.", code=404)
            if webhook_action == "add_members":
                services.add_cohort_members(cohort_or_none, identifiers)
            else:
                services.remove_cohort_members(cohort_or_none, identifiers)

        return Response({"action": webhook_action, "status": "success"})

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, ParseError):
            # A body that isn't valid JSON raises before post() runs, so the
            # response is shaped here to keep the envelope Mixpanel expects.
            return self._failure(self.request, message="Invalid payload.", code=400)
        if isinstance(exc, ValidationError):
            # Raised below the view, e.g. by the segment limit on cohort
            # creation; shaped here for the same reason.
            return self._failure(
                self.request,
                message=json.dumps(exc.detail, default=str),
                code=400,
            )
        return super().handle_exception(exc)

    def _failure(self, request: Request, *, message: str, code: int) -> Response:
        logger.warning(
            "sync_webhook.rejected",
            source="mixpanel",
            action=self._echo_action(request),
            environment__id=typing.cast(CohortSyncKey, request.auth).environment_id,
            error__message=message,
            error__code=code,
        )
        return Response(
            {
                "action": self._echo_action(request),
                "status": "failure",
                "error": {"message": message, "code": code},
            },
            status=code,
        )

    def _echo_action(self, request: Request) -> str | None:
        # Mixpanel expects the response to name the action it sent, even on
        # failure; None when the request was too malformed to carry one.
        if isinstance(request.data, dict) and isinstance(
            action_value := request.data.get("action"), str
        ):
            return action_value
        return None


@extend_schema_view(
    add=extend_schema(
        description=(
            "Add members to a CSV cohort. Accepted deltas are applied to "
            "identity data asynchronously. Re-adding a member is a no-op, "
            "so retries are safe."
        ),
        request=WebhookSyncMembersSerializer,
        responses={200: None},
    ),
    remove=extend_schema(
        description=(
            "Remove members from a CSV cohort. Accepted deltas are applied "
            "to identity data asynchronously. Removing a non-member is a "
            "no-op, so retries are safe."
        ),
        request=WebhookSyncMembersSerializer,
        responses={200: None},
    ),
)
class WebhookCohortSyncViewSet(viewsets.ViewSet):
    authentication_classes = [CohortSyncKeyAuthentication]
    permission_classes = [HasCohortSyncKey, CohortSyncPlanPermission]

    @action(detail=True, methods=["POST"], url_path="members/add")
    def add(self, request: Request, pk: str) -> Response:
        cohort = self._get_cohort(request, pk)
        serializer = WebhookSyncMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_cohort_members(cohort, serializer.validated_data["identifiers"])
        return Response()

    @action(detail=True, methods=["POST"], url_path="members/remove")
    def remove(self, request: Request, pk: str) -> Response:
        cohort = self._get_cohort(request, pk)
        serializer = WebhookSyncMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.remove_cohort_members(cohort, serializer.validated_data["identifiers"])
        return Response()

    def _get_cohort(self, request: Request, pk: str) -> Cohort:
        cohort = services.get_active_cohort(
            # HasCohortSyncKey has already established the type.
            environment=typing.cast(CohortSyncKey, request.auth).environment,
            source_type=CohortSourceType.CSV,
            uuid=pk,
        )
        if cohort is None:
            raise NotFound("Cohort not found.")
        return cohort
