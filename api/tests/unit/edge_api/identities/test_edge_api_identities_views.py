from rest_framework.permissions import IsAuthenticated

from edge_api.identities.views import EdgeIdentityViewSet
from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_ENVIRONMENT,
)
from environments.permissions.permissions import NestedEnvironmentPermissions


def test_edge_identity_view_set_get_permissions():
    # Given
    view_set = EdgeIdentityViewSet()

    # When
    permissions = view_set.get_permissions()

    # Then
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], NestedEnvironmentPermissions)

    assert permissions[1].action_permission_map == {
        "list": VIEW_ENVIRONMENT,
        "retrieve": MANAGE_IDENTITIES,
        "get_traits": MANAGE_IDENTITIES,
        "update_traits": MANAGE_IDENTITIES,
    }
