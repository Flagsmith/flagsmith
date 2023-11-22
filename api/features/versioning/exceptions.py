from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureVersioningError(APIException):
    pass


class FeatureVersionDeleteError(FeatureVersioningError):
    status_code = status.HTTP_400_BAD_REQUEST


class CannotModifyLiveVersionError(FeatureVersioningError):
    status_code = status.HTTP_400_BAD_REQUEST
