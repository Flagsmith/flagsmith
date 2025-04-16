import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.lead_tracking.hubspot.services import (
    create_self_hosted_onboarding_lead,
)
from onboarding.serializers import SelfHostedOnboardingSupportSerializer
from onboarding.tasks import send_onboarding_request_to_saas_flagsmith
from onboarding.throttling import OnboardingRequestThrottle
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_onboarding_request_to_saas_flagsmith_view(request: Request) -> Response:
    admin_user: FFAdminUser = request.user  # type: ignore[assignment]
    organisation = admin_user.organisations.first()

    if not organisation:
        return Response(
            {"error": "Please create an organisation before requesting support"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    send_onboarding_request_to_saas_flagsmith.delay(
        kwargs={
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "email": admin_user.email,
            "organisation_name": organisation.name,
        }
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


class ReceiveSupportRequestFromSelfHosted(GenericAPIView):  # type: ignore[type-arg]
    serializer_class = SelfHostedOnboardingSupportSerializer
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = [OnboardingRequestThrottle]

    def post(self, request: Request) -> Response:
        if not settings.HUBSPOT_ACCESS_TOKEN:
            return Response(
                {"error": "HubSpot access token not configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_self_hosted_onboarding_lead(**serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)
