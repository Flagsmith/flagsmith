from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidPlanIDError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Plan ID not found"


class InvalidAddonIDError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Subscription ID not found"
