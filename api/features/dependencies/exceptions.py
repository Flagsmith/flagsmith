from typing import TypedDict

from common.environments.permissions import MANAGE_SEGMENT_OVERRIDES
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied

from features.dependencies.types import DependencyPath, ReferencingEnvironment


class _DependencyConflictDetail(TypedDict):
    """The body served where existing dependencies refuse a change."""

    code: str
    message: str
    environment: ReferencingEnvironment
    path: DependencyPath


class DependencyConflictError(APIException):
    """Raised where existing dependencies refuse a change."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self, environment: ReferencingEnvironment, path: DependencyPath
    ) -> None:
        super().__init__()
        detail: _DependencyConflictDetail = {
            "code": self.default_code,
            "message": self.get_message(path),
            "environment": environment,
            "path": path,
        }
        self.detail = detail  # type: ignore[assignment]

    def get_message(self, path: DependencyPath) -> str:
        raise NotImplementedError()


class CircularDependencyError(DependencyConflictError):
    """Raised where a feature would end up depending on itself."""

    default_code = "circular_dependency"

    def get_message(self, path: DependencyPath) -> str:
        return f'The feature "{path[0]["feature"]["name"]}" would depend on itself.'


class PrerequisiteHasPrerequisiteError(DependencyConflictError):
    """Raised where the requested prerequisite depends on other features itself."""

    default_code = "prerequisite_has_prerequisite"

    def get_message(self, path: DependencyPath) -> str:
        prerequisite_edge = path[0]
        prerequisite_name = prerequisite_edge["feature"]["name"]
        prerequisite_of_prerequisite_name = prerequisite_edge["prerequisite"]["name"]
        return (
            f'The prerequisite "{prerequisite_name}" already has'
            f' a prerequisite "{prerequisite_of_prerequisite_name}".'
        )


class FeatureIsPrerequisiteError(DependencyConflictError):
    """Raised where the requested dependent feature is a prerequisite itself."""

    default_code = "feature_is_prerequisite"

    def get_message(self, path: DependencyPath) -> str:
        dependent_edge = path[0]
        feature_name = dependent_edge["prerequisite"]["name"]
        dependent_name = dependent_edge["feature"]["name"]
        return (
            f'The feature "{feature_name}" is already a prerequisite'
            f' for the feature "{dependent_name}".'
        )


class DependencyExistsError(DependencyConflictError):
    """Raised where the requested dependency is already in place."""

    default_code = "dependency_exists"

    def get_message(self, path: DependencyPath) -> str:
        existing_edge = path[0]
        return (
            f'The feature "{existing_edge["feature"]["name"]}" already depends'
            f' on the feature "{existing_edge["prerequisite"]["name"]}".'
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


class FeatureDependencyPermissionDeniedError(PermissionDenied):
    """Raised where a caller may not manage the environment's segment overrides."""

    def __init__(self) -> None:
        permission_name = MANAGE_SEGMENT_OVERRIDES.capitalize().replace("_", " ")
        super().__init__(
            {
                "code": self.default_code,
                "message": f'The permission "{permission_name}" is necessary'
                " to manage feature dependencies.",
            }
        )


class PrerequisiteIsSelfError(APIException):
    """Raised where a feature is requested as its own prerequisite."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "prerequisite_is_self"
    default_detail = "A feature cannot depend on itself."

    def __init__(self) -> None:
        super().__init__({"code": self.default_code, "message": self.default_detail})


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
