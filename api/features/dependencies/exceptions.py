from typing import TypedDict

from rest_framework import status
from rest_framework.exceptions import APIException

from features.dependencies.types import DependencyPath


class _CircularDependencyDetail(TypedDict):
    """The body served where a feature is refused for depending on itself."""

    code: str
    path: DependencyPath


class CircularDependencyError(APIException):
    """Raised where a feature would end up depending on itself."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "circular_dependency"

    def __init__(self, path: DependencyPath) -> None:
        super().__init__()
        detail: _CircularDependencyDetail = {"code": self.default_code, "path": path}
        self.detail = detail  # type: ignore[assignment]


class PrerequisiteFeatureNotFoundError(APIException):
    """Raised where a segment condition names a feature that does not exist."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "prerequisite_feature_not_found"

    def __init__(self, prerequisite_feature: str, condition_json_path: str) -> None:
        super().__init__(
            {
                "code": self.default_code,
                "prerequisite_feature": prerequisite_feature,
                "condition_json_path": condition_json_path,
            }
        )
