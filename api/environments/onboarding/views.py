from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment
from environments.onboarding.serializers import (
    EnvironmentOnboardingStatusSerializer,
    EnvironmentOnboardingStatusUpdateSerializer,
)
from environments.onboarding.services import record_environment_first_evaluation


class EnvironmentOnboardingStatusAPIView(RetrieveAPIView[Environment]):
    """Obtain information on whether features for this environment have been evaluated yet."""

    authentication_classes = ()
    permission_classes = ()
    throttle_classes = []

    queryset = Environment.objects.select_related("project")
    lookup_field = "api_key"
    lookup_url_kwarg = "environment_api_key"
    serializer_class = EnvironmentOnboardingStatusSerializer

    @extend_schema(exclude=True)
    def put(self, request: Request, environment_api_key: str) -> Response:
        """Mark this environment as having been evaluated by a client SDK."""
        serializer = EnvironmentOnboardingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record_environment_first_evaluation(
            environment=self.get_object(),
            sdk_label=serializer.validated_data["first_evaluated_sdk_label"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
