from app_analytics.track import track_feature_evaluation_influxdb
from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from telemetry.serializers import TelemetrySerializer

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions


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
        if settings.INFLUXDB_TOKEN:
            track_feature_evaluation_influxdb(request.environment.id, request.data)

        return Response(status=status.HTTP_200_OK)


class SelfHostedTelemetryAPIView(CreateAPIView):
    """
    Class to handle telemetry events from self hosted APIs so we can aggregate and track
    self hosted installation data
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = TelemetrySerializer
