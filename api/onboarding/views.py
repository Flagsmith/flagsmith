import logging

import requests
from django.conf import settings
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.lead_tracking.hubspot.service import (
    create_self_hosted_onboarding_lead,
)
from onboarding.serializers import SelfHostedOnboardingSupportSerializer

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_onboarding_request_to_saas_flagsmith_view(request: Request):
    # TODO: fix url
    url = "https://api.flagsmith.com//api/v1/onboarding/self-hosted-support/send/"
    admin_user = request.user
    organisation = admin_user.organisations.first()
    data = {
        "first_name": admin_user.first_name,
        "last_name": admin_user.last_name,
        "email": admin_user.email,
        "organisation_name": organisation.name,
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
    except RequestException as e:
        logger.error("Failed to send support request to flagsmith: %s", e)
        return Response(
            {"error": "Failed to send support request."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: Add rate limiting
@api_view(["POST"])
def receive_support_request_from_self_hosted_view(request: Request):
    if not settings.HUBSPOT_ACCESS_TOKEN:
        return Response(
            {"error": "HubSpot access token not configured."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = SelfHostedOnboardingSupportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    create_self_hosted_onboarding_lead(*serializer.data)
    return Response(status=status.HTTP_204_NO_CONTENT)
