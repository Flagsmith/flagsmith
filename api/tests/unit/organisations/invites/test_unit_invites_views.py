from rest_framework.permissions import IsAuthenticated

from organisations.invites.views import InviteLinkViewSet, InviteViewSet
from organisations.permissions.permissions import (
    MANAGE_USERS,
    HasOrganisationPermission,
)


def test_invite_view_set_get_permissions():
    permissions = InviteViewSet().get_permissions()
    assert len(permissions) == 2
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], HasOrganisationPermission)
    assert permissions[1].permission_key == MANAGE_USERS


def test_invite_link_view_set_get_permissions():
    permissions = InviteLinkViewSet().get_permissions()
    assert len(permissions) == 2
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], HasOrganisationPermission)
    assert permissions[1].permission_key == MANAGE_USERS
