from unittest import mock

from organisations.models import Organisation
from organisations.permissions.permissions import OrganisationUsersPermission
from users.models import FFAdminUser


def test_organisation_users_permission__list_action__allows_staff_user(
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
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_organisation_users_permission__create_action__denies_staff_user(
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
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False
