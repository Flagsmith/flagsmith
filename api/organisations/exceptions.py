from rest_framework.exceptions import APIException


class OrganisationHasNoSubscription(APIException):
    status_code = 400
    default_detail = "Organisation has no subscription"
