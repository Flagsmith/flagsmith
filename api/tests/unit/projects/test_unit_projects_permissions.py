import pytest
from rest_framework.exceptions import APIException, PermissionDenied

from projects.permissions import IsProjectAdmin


def test_is_project_admin_has_permission_raises_permission_denied_if_not_found(
    mocker, admin_user
):
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": 1})

    # Then
    with pytest.raises(PermissionDenied):
        IsProjectAdmin().has_permission(request, view)


def test_is_project_admin_has_permission_raises_api_exception_if_no_kwarg(
    mocker, admin_user
):
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"foo": "bar"})

    # Then
    with pytest.raises(APIException):
        IsProjectAdmin().has_permission(request, view)


def test_is_project_admin_has_permission_returns_true_if_project_admin(
    mocker, admin_user, organisation, project
):
    # Given
    assert admin_user.is_project_admin(project)
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": project.id})

    # Then
    assert IsProjectAdmin().has_permission(request, view)
