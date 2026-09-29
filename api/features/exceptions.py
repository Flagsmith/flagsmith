from rest_framework import status
from rest_framework.exceptions import APIException, NotFound


class FeatureStateVersionError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class FeatureStateVersionAlreadyExistsError(FeatureStateVersionError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, version: int):
        super(FeatureStateVersionAlreadyExistsError, self).__init__(
            f"Version {version} already exists for FeatureState."
        )


class FeatureNotFoundError(NotFound):
    """Raised where a feature ID is not in the environment's project."""

    default_code = "feature_not_found"

    def __init__(self, feature_id: int) -> None:
        super().__init__(
            {
                "code": self.default_code,
                "message": f"Feature ID '{feature_id}' does not exist in the project.",
            }
        )
