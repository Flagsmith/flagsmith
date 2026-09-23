from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureVersioningError(APIException):
    pass


class FeatureVersionDeleteError(FeatureVersioningError):
    status_code = status.HTTP_400_BAD_REQUEST


class CannotModifyLiveVersionError(FeatureVersioningError):
    status_code = status.HTTP_400_BAD_REQUEST


class DirectFeatureStateWriteNotAllowedError(FeatureVersioningError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "direct_feature_state_write_not_allowed"
    default_detail = "This environment uses v2 feature versioning. Use the environment feature version endpoint instead."
