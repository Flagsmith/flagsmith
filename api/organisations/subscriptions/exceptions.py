from rest_framework.exceptions import APIException


class InvalidSubscriptionPlanError(APIException):
    status_code = 403
    default_detail = "Organisation does not have a valid plan for this resource."


class CannotCancelChargebeeSubscription(APIException):
    default_detail = "Unable to cancel subscription in Chargebee"
