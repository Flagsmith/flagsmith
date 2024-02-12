import logging

from app_analytics.analytics_db_service import (
    get_total_events_count,
    get_usage_data,
)
from app_analytics.tasks import (
    track_feature_evaluation,
    track_feature_evaluation_v2,
)
from app_analytics.track import (
    track_feature_evaluation_influxdb,
    track_feature_evaluation_influxdb_v2,
)
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.fields import IntegerField
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from telemetry.serializers import TelemetrySerializer

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.models import FeatureState
from organisations.models import Organisation

from .permissions import UsageDataPermission
from .serializers import (
    SDKAnalyticsFlagsSerializer,
    UsageDataQuerySerializer,
    UsageDataSerializer,
    UsageTotalCountSerializer,
)

logger = logging.getLogger(__name__)


class SDKAnalyticsFlagsV2(CreateAPIView):
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = SDKAnalyticsFlagsSerializer
    throttle_classes = []

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.evaluations = serializer.validated_data["evaluations"]
        if not self._is_data_valid():
            return Response(
                {"detail": "Invalid feature names associated with the project."},
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if settings.USE_POSTGRES_FOR_ANALYTICS:
            track_feature_evaluation_v2.delay(
                args=(
                    request.environment.id,
                    self.evaluations,
                )
            )
        elif settings.INFLUXDB_TOKEN:
            track_feature_evaluation_influxdb_v2.delay(
                args=(
                    request.environment.id,
                    self.evaluations,
                )
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _is_data_valid(self) -> bool:
        environment_feature_names = set(
            FeatureState.objects.filter(
                environment=self.request.environment,
                feature_segment=None,
                identity=None,
            ).values_list("feature__name", flat=True)
        )

        valid = True
        for evaluation in self.evaluations:
            if evaluation["feature_name"] in environment_feature_names:
                continue
            logger.warning(
                f"Feature {evaluation['feature_name']} does not belong to project"
            )
            valid = False

        return valid


class SDKAnalyticsFlags(GenericAPIView):
    """
    Class to handle flag analytics events
    """

    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    throttle_classes = []

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False):
            return Serializer

        environment_feature_names = set(
            FeatureState.objects.filter(
                environment=self.request.environment,
                feature_segment=None,
                identity=None,
            ).values_list("feature__name", flat=True)
        )

        class _AnalyticsSerializer(Serializer):
            def get_fields(self):
                return {
                    feature_name: IntegerField(required=False)
                    for feature_name in environment_feature_names
                }

        return _AnalyticsSerializer

    def post(self, request, *args, **kwargs):
        """
        Send flag evaluation events from the SDK back to the API for reporting.


        TODO: Eventually replace this with the v2 version of
              this endpoint once SDKs have been updated.
        """
        is_valid = self._is_data_valid()
        if not is_valid:
            # for now, return 200 to avoid breaking client integrations
            return Response(
                {"detail": "Invalid data. Not logged."},
                content_type="application/json",
                status=status.HTTP_200_OK,
            )

        if settings.USE_POSTGRES_FOR_ANALYTICS:
            track_feature_evaluation.delay(
                args=(
                    request.environment.id,
                    request.data,
                )
            )
        elif settings.INFLUXDB_TOKEN:
            track_feature_evaluation_influxdb.delay(
                args=(
                    request.environment.id,
                    request.data,
                )
            )

        return Response(status=status.HTTP_200_OK)

    def _is_data_valid(self) -> bool:
        environment_feature_names = set(
            FeatureState.objects.filter(
                environment=self.request.environment,
                feature_segment=None,
                identity=None,
            ).values_list("feature__name", flat=True)
        )

        is_valid = True
        for feature_name, request_count in self.request.data.items():
            if not (
                isinstance(feature_name, str)
                and feature_name in environment_feature_names
            ):
                logger.warning("Feature %s does not belong to project", feature_name)
                is_valid = False

            if not (isinstance(request_count, int)):
                logger.error(
                    "Analytics data contains non integer request count. User agent: %s",
                    self.request.headers.get("User-Agent", "Not found"),
                )
                is_valid = False

        return is_valid


class SelfHostedTelemetryAPIView(CreateAPIView):
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
def get_usage_data_total_count_view(request, organisation_pk=None):
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
def get_usage_data_view(request, organisation_pk=None):
    filters = UsageDataQuerySerializer(data=request.query_params)
    filters.is_valid(raise_exception=True)

    organisation = Organisation.objects.get(id=organisation_pk)
    usage_data = get_usage_data(organisation, **filters.data)
    serializer = UsageDataSerializer(usage_data, many=True)

    return Response(serializer.data)
