import pytest

from organisations.permissions.permissions import (
    MANAGE_USER_GROUPS,
    MANAGE_USERS,
    HasOrganisationPermission,
    OrganisationPermission,
    UserPermissionGroupPermission,
)


@pytest.mark.parametrize(
    "has_organisation_permission, expected_result", ((True, True), (False, False))
)
def test_has_organisation_permission(
    mocker, organisation, has_organisation_permission, expected_result
):
    # Given
    permission_key = "PERMISSION_KEY"
    permission_class = HasOrganisationPermission(permission_key=permission_key)

    mock_view = mocker.MagicMock()
    mock_user = mocker.MagicMock()
    mock_request = mocker.MagicMock(user=mock_user)
    mock_user.has_organisation_permission.return_value = has_organisation_permission
    mock_view.kwargs = {"organisation_pk": organisation.id}

    # When
    result = permission_class.has_permission(mock_request, mock_view)

    # Then
    assert result is expected_result
    mock_user.has_organisation_permission.assert_called_once_with(
        organisation=organisation, permission_key=permission_key
    )


@pytest.mark.parametrize("action", ("invite", "remove-users"))
def test_organisation_permission_allows_users_with_manage_users_to_manage_users(
    organisation, mocker, action
):
    # Given
    permission_class = OrganisationPermission()

    mock_user = mocker.MagicMock()
    mock_request = mocker.MagicMock(user=mock_user)
    mock_view = mocker.MagicMock(action=action)
    mock_view.get_object.return_value = organisation

    mock_user.has_organisation_permission.side_effect = (
        lambda o, perm_key: o == organisation and perm_key == MANAGE_USERS
    )

    # When
    result = permission_class.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_user_organisation_permissions_has_permission_allows_organisation_members_to_list_groups(
    organisation_one, organisation_one_user, mocker
):
    # Given
    permissions = UserPermissionGroupPermission()

    mock_request = mocker.MagicMock(user=organisation_one_user)
    mock_view = mocker.MagicMock(
        kwargs={"organisation_pk": organisation_one.id}, action="list"
    )

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_user_organisation_permissions_has_permission_permits_users_with_manage_groups(
    organisation, mocker
):
    # Given
    permissions = UserPermissionGroupPermission()

    mock_user = mocker.MagicMock()
    mock_request = mocker.MagicMock(user=mock_user)
    mock_view = mocker.MagicMock(kwargs={"organisation_pk": organisation.id})

    mock_user.has_organisation_permission.side_effect = (
        lambda o, perm: o == organisation and perm == MANAGE_USER_GROUPS
    )

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_user_organisation_permissions_has_object_permission_permits_users_with_manage_groups(
    organisation, mocker
):
    # Given
    permissions = UserPermissionGroupPermission()

    mock_user = mocker.MagicMock()
    mock_request = mocker.MagicMock(user=mock_user)
    mock_view = mocker.MagicMock(kwargs={"organisation_pk": organisation.id})

    mock_user.has_organisation_permission.side_effect = (
        lambda o, perm: o == organisation and perm == MANAGE_USER_GROUPS
    )

    # When
    result = permissions.has_object_permission(mock_request, mock_view, organisation)

    # Then
    assert result is True
