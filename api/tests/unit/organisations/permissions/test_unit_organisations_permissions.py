from unittest import mock

from organisations.models import Organisation
from organisations.permissions.permissions import OrganisationUsersPermission
from users.models import FFAdminUser


def test_org_user_can_list_users(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="list",
        kwargs={"organisation_pk": organisation.id},
    )
    permissions = OrganisationUsersPermission()

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_org_user_cannot_create_user(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="create",
        kwargs={"organisation_pk": organisation.id},
    )
    permissions = OrganisationUsersPermission()

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False
