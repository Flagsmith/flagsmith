from common.environments.permissions import (
    CREATE_CHANGE_REQUEST,
    MANAGE_SEGMENT_OVERRIDES,
)

from environments.models import Environment
from features.dependencies.exceptions import (
    ChangeRequestPermissionDeniedError,
    FeatureDependencyPermissionDeniedError,
)
from features.future.permissions import check_read_permissions
from users.abc import UserABC


def check_manage_permissions(user: UserABC, environment: Environment) -> None:
    """Authorise a caller to manage the environment's feature dependencies."""
    check_read_permissions(user, environment)
    if not user.has_environment_permission(MANAGE_SEGMENT_OVERRIDES, environment):
        raise FeatureDependencyPermissionDeniedError()


def check_change_request_permissions(user: UserABC, environment: Environment) -> None:
    """Authorise a caller to change the environment's feature dependencies in change requests."""
    if not user.has_environment_permission(CREATE_CHANGE_REQUEST, environment):
        raise ChangeRequestPermissionDeniedError()
