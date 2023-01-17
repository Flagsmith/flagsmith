import logging

from app_analytics.tasks import track_feature_evaluation
from app_analytics.track import track_feature_evaluation_influxdb
from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from telemetry.serializers import TelemetrySerializer

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.models import FeatureState

logger = logging.getLogger(__name__)


class SDKAnalyticsFlags(GenericAPIView):
    """
    Class to handle flag analytics events
    """

    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Send flag evaluation events from the SDK back to the API for reporting.
        """
        is_valid = self._is_data_valid()
        if not is_valid:
            # for now, return 200 to avoid breaking client integrations
            return Response(
                {"detail": "Invalid data. Not logged."},
                content_type="application/json",
                status=status.HTTP_200_OK,
            )
        if settings.USE_CUSTOM_ANALYTICS:
            track_feature_evaluation.delay(args=(request.environment.id, request.data))

        if settings.INFLUXDB_TOKEN:
            track_feature_evaluation_influxdb(request.environment.id, request.data)

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
    serializer_class = TelemetrySerializer
