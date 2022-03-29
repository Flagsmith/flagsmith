from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureWorkflowError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ChangeRequestNotApprovedError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST


class ChangeRequestNotValid(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST
