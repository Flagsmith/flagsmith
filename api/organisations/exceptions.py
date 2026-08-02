from rest_framework import status
from rest_framework.exceptions import APIException


class OrganisationHasNoPaidSubscription(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_code = "invalid-plan"
    default_detail = (
        "Organisation has no subscription. "
        "Please upgrade your plan: https://www.flagsmith.com/pricing"
    )
