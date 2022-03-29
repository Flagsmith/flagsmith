from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureStateVersionError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class FeatureStateVersionAlreadyExistsError(FeatureStateVersionError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, version: int):
        super(FeatureStateVersionAlreadyExistsError, self).__init__(
            f"Version {version} already exists for FeatureState."
        )
