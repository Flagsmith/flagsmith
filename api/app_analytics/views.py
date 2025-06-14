import logging
import typing

from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.fields import IntegerField
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from app_analytics.analytics_db_service import (
    get_total_events_count,
    get_usage_data,
)
from app_analytics.cache import FeatureEvaluationCache
from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.models import FeatureState
from organisations.models import Organisation
from telemetry.serializers import TelemetrySerializer

from .permissions import UsageDataPermission
from .serializers import (
    SDKAnalyticsFlagsSerializer,
    UsageDataQuerySerializer,
    UsageDataSerializer,
    UsageTotalCountSerializer,
)

logger = logging.getLogger(__name__)
feature_evaluation_cache = FeatureEvaluationCache()  # type: ignore[no-untyped-call]


class SDKAnalyticsFlagsV2(CreateAPIView):  # type: ignore[type-arg]
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = SDKAnalyticsFlagsSerializer
    throttle_classes = []

    @swagger_auto_schema(  # type: ignore[misc]
        request_body=SDKAnalyticsFlagsSerializer(),
        responses={204: Response(status=status.HTTP_204_NO_CONTENT)},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(environment=self.request.environment)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SDKAnalyticsFlags(CreateAPIView):  # type: ignore[type-arg]
    """
    Class to handle flag analytics events
    """

    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    throttle_classes = []
    format_kwarg = None

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return Serializer

        environment_feature_names = set(
            FeatureState.objects.filter(
                environment=self.request.environment,
                feature_segment=None,
                identity=None,
            ).values_list("feature__name", flat=True)
        )

        class _AnalyticsSerializer(Serializer):  # type: ignore[type-arg]
            def get_fields(self):  # type: ignore[no-untyped-def]
                return {
                    feature_name: IntegerField(required=False)
                    for feature_name in environment_feature_names
                }

            def save(self, **kwargs: typing.Any) -> None:
                request = self.context["request"]
                for feature_name, eval_count in self.validated_data.items():
                    feature_evaluation_cache.track_feature_evaluation(
                        request.environment.id, feature_name, eval_count
                    )

        return _AnalyticsSerializer

    @swagger_auto_schema(  # type: ignore[misc]
        request_body=SDKAnalyticsFlagsSerializer(),
        responses={200: Response(status=status.HTTP_200_OK)},
    )
    def create(
        self, request: Request, *args: typing.Any, **kwargs: typing.Any
    ) -> Response:
        """
        Send flag evaluation events from the SDK back to the API for reporting.

        TODO: Eventually replace this with the v2 version of
              this endpoint once SDKs have been updated.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        serializer.save(environment=self.request.environment)
        return Response(status=status.HTTP_200_OK)


class SelfHostedTelemetryAPIView(CreateAPIView):  # type: ignore[type-arg]
    """
    Class to handle telemetry events from self hosted APIs so we can aggregate and track
    self hosted installation data
    """

    permission_classes = ()
    authentication_classes = ()
    throttle_classes = []
    serializer_class = TelemetrySerializer


@swagger_auto_schema(
    responses={200: UsageTotalCountSerializer()},
    methods=["GET"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, UsageDataPermission])
def get_usage_data_total_count_view(request, organisation_pk=None):  # type: ignore[no-untyped-def]
    organisation = Organisation.objects.get(id=organisation_pk)
    count = get_total_events_count(organisation)
    serializer = UsageTotalCountSerializer(data={"count": count})
    serializer.is_valid(raise_exception=True)

    return Response(serializer.data)


@swagger_auto_schema(
    query_serializer=UsageDataQuerySerializer(),
    responses={200: UsageDataSerializer()},
    methods=["GET"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, UsageDataPermission])
def get_usage_data_view(request, organisation_pk=None):  # type: ignore[no-untyped-def]
    filters = UsageDataQuerySerializer(data=request.query_params)
    filters.is_valid(raise_exception=True)

    organisation = Organisation.objects.get(id=organisation_pk)
    usage_data = get_usage_data(organisation, **filters.data)
    serializer = UsageDataSerializer(usage_data, many=True)

    return Response(serializer.data)
