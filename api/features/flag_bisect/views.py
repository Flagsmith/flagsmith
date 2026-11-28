import typing

from django.conf import settings
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.pagination import CustomPagination
from core.dataclasses import AuthorData
from environments.authentication import EnvironmentKeyAuthentication
from environments.models import Environment
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.flag_bisect import services
from features.flag_bisect.models import Incident, SignalSource
from features.flag_bisect.permissions import FlagBisectPermission
from features.flag_bisect.serializers import (
    EnvelopeSerializer,
    IncidentListSerializer,
    IncidentSerializer,
    ReasonSerializer,
    SignalSourceResponseSerializer,
    SignalSourceSerializer,
    SignalsRequestSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["mcp"],
        operation_id="list_flag_bisect_incidents",
        description="Lists Flag Bisect incidents for an environment, newest first, with their state, "
        "rounds and conclusion.",
    ),
    retrieve=extend_schema(
        tags=["mcp"],
        operation_id="get_flag_bisect_incident",
        description="Retrieves a Flag Bisect incident: suspected flag changes and their odds, canary "
        "probes and verdicts, and the swarm's trail. Approvals stay with people.",
    ),
)
class IncidentViewSet(
    viewsets.GenericViewSet[Incident],
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """Flag Bisect incidents for one environment, and the two human gates."""

    permission_classes = [IsAuthenticated, FlagBisectPermission]
    pagination_class = CustomPagination
    lookup_field = "id"
    lookup_url_kwarg = "incident_id"

    def get_queryset(self) -> QuerySet[Incident]:
        return Incident.objects.filter(
            environment__api_key=self.kwargs.get("environment_api_key")
        )

    def get_serializer_class(self) -> typing.Any:
        return IncidentListSerializer if self.action == "list" else IncidentSerializer

    def _done(self, incident: Incident) -> Response:
        incident.refresh_from_db()
        return Response(IncidentSerializer(incident).data)

    @extend_schema(request=EnvelopeSerializer, responses=IncidentSerializer)
    @action(detail=True, methods=["post"], url_path="approve-envelope")
    def approve_envelope(self, request: Request, **kwargs: typing.Any) -> Response:
        serializer = EnvelopeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident = services.approve_envelope(
            self.get_object(),
            AuthorData.from_request(request),
            **serializer.validated_data,
        )
        return self._done(incident)

    @extend_schema(request=ReasonSerializer, responses=IncidentSerializer)
    @action(detail=True, methods=["post"])
    def abort(self, request: Request, **kwargs: typing.Any) -> Response:
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident = services.abort(
            self.get_object(),
            AuthorData.from_request(request),
            serializer.validated_data["reason"],
        )
        return self._done(incident)

    @extend_schema(request=None, responses=IncidentSerializer)
    @action(detail=True, methods=["post"], url_path="propose-remediation")
    def propose_remediation(self, request: Request, **kwargs: typing.Any) -> Response:
        incident = services.propose_remediation(
            self.get_object(), AuthorData.from_request(request)
        )
        return self._done(incident)

    @extend_schema(request=None, responses=IncidentSerializer)
    @action(detail=True, methods=["post"], url_path="approve-remediation")
    def approve_remediation(self, request: Request, **kwargs: typing.Any) -> Response:
        incident = services.approve_remediation(
            self.get_object(), AuthorData.from_request(request)
        )
        return self._done(incident)


class SDKFlagBisectSignalsView(APIView):
    """Request outcomes from your servers. Server-side environment keys only."""

    permission_classes = (EnvironmentKeyPermissions,)
    parser_classes = (JSONParser,)
    throttle_classes = []

    def get_authenticators(self) -> list[BaseAuthentication]:
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    @extend_schema(request=SignalsRequestSerializer, responses={202: None})
    def post(self, request: Request) -> Response:
        if not settings.FLAG_BISECT_ENABLED:
            raise NotFound()
        serializer = SignalsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signals = [
            services.Signal(identifier=s["identifier"], ok=s["ok"])
            for s in serializer.validated_data["signals"]
        ]
        services.record_signals(request.environment, signals)
        return Response(status=status.HTTP_202_ACCEPTED)


class SignalSourceView(APIView):
    """Which Experimentation events count as outcomes for this environment."""

    permission_classes = [IsAuthenticated, FlagBisectPermission]

    def _environment(self) -> Environment:
        environment: Environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        return environment

    @extend_schema(responses=SignalSourceResponseSerializer)
    def get(self, request: Request, **kwargs: typing.Any) -> Response:
        return Response(services.describe_signal_source(self._environment()))

    @extend_schema(
        request=SignalSourceSerializer, responses=SignalSourceResponseSerializer
    )
    def put(self, request: Request, **kwargs: typing.Any) -> Response:
        serializer = SignalSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        environment = self._environment()
        services.set_signal_source(environment, **serializer.validated_data)
        return Response(services.describe_signal_source(environment))

    @extend_schema(request=None, responses={204: None})
    def delete(self, request: Request, **kwargs: typing.Any) -> Response:
        SignalSource.objects.filter(environment=self._environment()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
