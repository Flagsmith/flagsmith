from rest_framework.exceptions import APIException


class OrganisationHasNoPaidSubscription(APIException):
    status_code = 400
    default_detail = "Organisation has no subscription"


class SubscriptionNotFound(APIException):
    status_code = 404
    default_detail = "Subscription Not found"
