"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Mapping

from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
    UPDATE_FEATURE_STATE,
)
from rest_framework.exceptions import NotFound, PermissionDenied

from environments.models import Environment
from users.abc import UserABC

PROPERTY_PERMISSIONS = {
    "environment_default": UPDATE_FEATURE_STATE,
    "segment_overrides": MANAGE_SEGMENT_OVERRIDES,
}


def check_update_permissions(
    user: UserABC, environment: Environment, properties: Mapping[str, object]
) -> None:
    """Authorise a caller to write the flag properties they sent.

    A caller who may write no property at all is not told the environment exists.
    """
    denied = {
        property_name
        for property_name, permission in PROPERTY_PERMISSIONS.items()
        if not user.has_environment_permission(permission, environment)
    }
    if len(denied) == len(PROPERTY_PERMISSIONS):
        raise NotFound()
    if any(property_name in properties for property_name in denied):
        raise PermissionDenied()
