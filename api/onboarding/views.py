import logging

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import ErrorSerializer
from integrations.lead_tracking.hubspot.tasks import (
    create_self_hosted_onboarding_lead_task,
)
from onboarding.serializers import (
    SelfHostedOnboardingReceiveSupportSerializer,
    SelfHostedOnboardingSupportSendRequestSerializer,
)
from onboarding.tasks import send_onboarding_request_to_saas_flagsmith_task
from onboarding.throttling import OnboardingRequestThrottle
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method="post",
    request_body=SelfHostedOnboardingSupportSendRequestSerializer,
    responses={204: "No Content", 400: ErrorSerializer()},
)  # type: ignore[misc]
@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_onboarding_request_to_saas_flagsmith_view(request: Request) -> Response:
    admin_user: FFAdminUser = request.user  # type: ignore[assignment]
    organisation = admin_user.organisations.first()

    if not organisation:
        return Response(
            {"message": "Please create an organisation before requesting support"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    send_onboarding_request_to_saas_flagsmith_task.delay(
        kwargs={
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "email": admin_user.email,
            "hubspot_cookie": request.data.get("hubspotutk"),
        }
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


class ReceiveSupportRequestFromSelfHosted(GenericAPIView):  # type: ignore[type-arg]
    serializer_class = SelfHostedOnboardingReceiveSupportSerializer
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = [OnboardingRequestThrottle]

    @swagger_auto_schema(
        request_body=SelfHostedOnboardingReceiveSupportSerializer,
        responses={204: "No Content", 400: ErrorSerializer()},
    )  # type: ignore[misc]
    def post(self, request: Request) -> Response:
        if not settings.HUBSPOT_ACCESS_TOKEN:
            return Response(
                {"message": "HubSpot access token not configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_self_hosted_onboarding_lead_task.delay(kwargs=serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)
