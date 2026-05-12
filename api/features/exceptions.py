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


class FeatureStateV2VersioningRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "v2_feature_versioning_required"

    def __init__(
        self, environment_api_key: str, feature_id: int | None = None
    ) -> None:
        feature_path = str(feature_id) if feature_id is not None else "<feature-id>"
        super().__init__(
            detail=(
                "This environment uses v2 feature versioning. Create a new "
                "environment feature version via POST /api/v1/environments/"
                f"{environment_api_key}/features/{feature_path}/versions/."
            )
        )
