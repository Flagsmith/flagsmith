import logging
import typing

from common.core.utils import using_database_replica
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from app_analytics.analytics_db_service import (
    get_total_events_count,
    get_usage_data,
)
from app_analytics.cache import FeatureEvaluationCache
from app_analytics.throttles import InfluxQueryThrottle
from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from organisations.models import Organisation
from telemetry.serializers import TelemetrySerializer

from .permissions import UsageDataPermission
from .serializers import (
    SDKAnalyticsFlagsSerializer,
    SDKAnalyticsFlagsV1Serializer,
    UsageDataQuerySerializer,
    UsageDataSerializer,
    UsageTotalCountSerializer,
)

logger = logging.getLogger(__name__)
feature_evaluation_cache = FeatureEvaluationCache()


class SDKAnalyticsFlagsV2(CreateAPIView):  # type: ignore[type-arg]
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = SDKAnalyticsFlagsSerializer
    throttle_classes = []

    @extend_schema(
        request=SDKAnalyticsFlagsSerializer,
        responses={204: None},
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
    serializer_class = SDKAnalyticsFlagsV1Serializer
    throttle_classes = []

    @extend_schema(
        request=SDKAnalyticsFlagsSerializer,
        responses={200: None},
    )
    def create(
        self, request: Request, *args: typing.Any, **kwargs: typing.Any
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(environment=request.environment, cache=feature_evaluation_cache)
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


@extend_schema(responses={200: UsageTotalCountSerializer})
@api_view(["GET"])
@permission_classes([IsAuthenticated, UsageDataPermission])
@throttle_classes([InfluxQueryThrottle])
def get_usage_data_total_count_view(request: Request, organisation_pk: int) -> Response:
    organisation = using_database_replica(Organisation.objects).get(id=organisation_pk)
    count = get_total_events_count(organisation)
    serializer = UsageTotalCountSerializer(data={"count": count})
    serializer.is_valid(raise_exception=True)

    return Response(serializer.data)


@extend_schema(
    parameters=[UsageDataQuerySerializer],
    responses={200: UsageDataSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, UsageDataPermission])
@throttle_classes([InfluxQueryThrottle])
def get_usage_data_view(request: Request, organisation_pk: int) -> Response:
    filters = UsageDataQuerySerializer(data=request.query_params)
    filters.is_valid(raise_exception=True)

    organisation = using_database_replica(Organisation.objects).get(id=organisation_pk)
    usage_data = get_usage_data(organisation, **filters.validated_data)
    serializer = UsageDataSerializer(usage_data, many=True)

    return Response(serializer.data)
