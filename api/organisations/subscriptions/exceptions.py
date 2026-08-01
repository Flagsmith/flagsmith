from rest_framework import status
from rest_framework.exceptions import APIException


class BaseInvalidPlanError(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_code = "invalid-plan"
    default_detail = (
        "Organisation does not have a valid plan for this resource. "
        "Please upgrade your plan: https://www.flagsmith.com/pricing"
    )


class InvalidSubscriptionPlanError(BaseInvalidPlanError):
    pass


class CannotCancelChargebeeSubscription(APIException):
    default_detail = "Unable to cancel subscription in Chargebee"


class UpgradeSeatsError(APIException):
    default_detail = "Failed to upgrade seats in Chargebee"


class UpgradeSeatsPaymentFailure(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Joining the organisation has failed due to a payment issue. "
        "Please contact your organisation's admin."
    )


class UpgradeAPIUsageError(APIException):
    default_detail = "Failed to upgrade API use in Chargebee"


class UpgradeAPIUsagePaymentFailure(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "API usage upgrade has failed due to a payment issue. "
        "If this persists, contact the organisation admin."
    )


class SubscriptionDoesNotSupportSeatUpgrade(BaseInvalidPlanError):
    default_detail = (
        "Please upgrade your plan to add additional seats/users: "
        "https://www.flagsmith.com/pricing"
    )