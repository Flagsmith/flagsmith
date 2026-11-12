from rest_framework.exceptions import APIException


class OrganisationHasNoPaidSubscription(APIException):
    status_code = 400
    default_detail = "Organisation has no subscription"
