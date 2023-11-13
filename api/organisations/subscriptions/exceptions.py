from rest_framework.exceptions import APIException


class InvalidSubscriptionPlanError(APIException):
    status_code = 403
    default_detail = "Organisation does not have a valid plan for this resource."


class CannotCancelChargebeeSubscription(APIException):
    default_detail = "Unable to cancel subscription in Chargebee"


class UpgradeSeatsError(APIException):
    default_detail = "Failed to upgrade seats in Chargebee"


class UpgradeSeatsPaymentFailure(APIException):
    status_code = 400
    default_detail = (
        "Joining the organisation has failed due to a payment issue. "
        "Please contact your organisation's admin."
    )


class SubscriptionDoesNotSupportSeatUpgrade(APIException):
    status_code = 400
    default_detail = "Please Upgrade your plan to add additional seats/users"
