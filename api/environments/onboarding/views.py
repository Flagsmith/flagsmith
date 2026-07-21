from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from environments.onboarding.serializers import (
    EnvironmentOnboardingStatusSerializer,
    EnvironmentOnboardingStatusUpdateSerializer,
)
from environments.onboarding.tasks import record_environment_first_evaluation


class EnvironmentOnboardingStatusAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = []

    def get(self, _: Request, environment_api_key: str) -> Response:
        """Obtain information on whether features for this environment have been evaluated yet."""
        environment = (
            Environment.objects.select_related(None)
            .only(
                "first_evaluated_at",
                "first_evaluated_sdk_label",
            )
            .get(api_key=environment_api_key)
        )
        serializer = EnvironmentOnboardingStatusSerializer(environment)
        return Response(serializer.data)

    def put(self, request: Request, environment_api_key: str) -> Response:
        """Mark this environment as having been evaluated by a client SDK."""
        serializer = EnvironmentOnboardingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record_environment_first_evaluation.delay(
            args=(
                environment_api_key,
                serializer.validated_data["first_evaluated_sdk_label"],
            ),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
