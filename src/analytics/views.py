from django.utils.decorators import method_decorator
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions

from analytics.track import track_feature_evaluation_influxdb


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
        track_feature_evaluation_influxdb(request.environment.id, request.data)
        return Response(status=status.HTTP_200_OK)
