import os
from unittest import mock

import pytest
from common.projects.permissions import VIEW_PROJECT
from django.conf import settings
from rest_framework.exceptions import APIException, PermissionDenied

from organisations.models import Organisation, OrganisationRole
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import Project, UserPermissionGroupProjectPermission
from projects.permissions import IsProjectAdmin, ProjectPermissions
from tests.types import (
    WithOrganisationPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser, UserPermissionGroup

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()


def test_list_project_has_permission(
    staff_user: FFAdminUser,
) -> None:
    """All users should be able to create project"""
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="list", detail=False)
    project_permissions = ProjectPermissions()

    # When
    response = project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert response is True


def test_create_project_has_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    with_organisation_permissions: WithOrganisationPermissionsCallable,
) -> None:
    # Given
    with_organisation_permissions([CREATE_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(
        user=staff_user, data={"name": "Test", "organisation": organisation.id}
    )
    mock_view = mock.MagicMock(action="create", detail=False)
    project_permissions = ProjectPermissions()

    # When
    response = project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert response is True


def test_create_project_has_permission_with_e2e_test_auth_token(
    staff_user: FFAdminUser,
    organisation: Organisation,
    with_organisation_permissions: WithOrganisationPermissionsCallable,
) -> None:
    # Given
    with_organisation_permissions([CREATE_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(
        user=staff_user, data={"name": "Test", "organisation": organisation.id}
    )
    token = "test-token"
    settings.ENABLE_FE_E2E = True
    os.environ["E2E_TEST_AUTH_TOKEN"] = token

    mock_request.META = {"E2E_TEST_AUTH_TOKEN": token}
    mock_view = mock.MagicMock(action="create", detail=False)
    project_permissions = ProjectPermissions()

    # When
    response = project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert response is True


def test_admin_can_update_project_has_permission(
    organisation: Organisation,
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="update", detail=True)
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result is True


def test_admin_group_can_update_project_has_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="update", detail=True)

    user_permission_group = UserPermissionGroup.objects.create(
        name="Users", organisation=organisation
    )
    user_permission_group.users.add(staff_user)
    UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, admin=True, project=project
    )
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result is True


def test_regular_user_cannot_update_project_missing_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="update", detail=True)
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result is False


def test_admin_can_delete_project_has_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Users", organisation=organisation
    )
    user_permission_group.users.add(staff_user)
    UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, admin=True, project=project
    )
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="destroy", detail=True)
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result is True


def test_regular_user_cannot_delete_project(
    staff_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="destroy", detail=True)
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result is False


def test_organisation_admin_can_perform_all_actions_on_a_project(
    admin_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    list_actions = ("list", "create")
    detail_actions = ("update", "destroy", "delete", "retrieve")
    mock_request = mock.MagicMock(
        user=admin_user, data={"name": "Test", "organisation": organisation.id}
    )
    project_permissions = ProjectPermissions()

    # When
    results = []
    for action in list_actions:
        mock_view.action = action
        mock_view.detail = False
        results.append(project_permissions.has_permission(mock_request, mock_view))  # type: ignore[no-untyped-call]

    for action in detail_actions:
        mock_view.action = action
        mock_view.detail = True
        results.append(
            project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501
        )

    # Then
    assert all(result for result in results)


def test_user_with_view_project_permission_can_view_project(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(action="retrieve")
    project_permissions = ProjectPermissions()

    # When
    result = project_permissions.has_object_permission(mock_request, mock_view, project)  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert result


def test_project_admin_has_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(detail=False, kwargs={"project_pk": project.id})
    actions = ["list", "create"]
    permissions = IsProjectAdmin()

    # When
    results = []
    for action in actions:
        mock_view.action = action
        results.append(permissions.has_permission(mock_request, mock_view))  # type: ignore[no-untyped-call]

    # Then
    assert all(results)


def test_project_admin_has_object_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    upp = with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(detail=True, kwargs={"project_pk": project.id})
    actions = ["update", "destroy"]
    permissions = IsProjectAdmin()

    # When
    results = []
    for action in actions:
        mock_view.action = action
        results.append(permissions.has_object_permission(mock_request, mock_view, upp))  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert all(results)


def test_organisation_admin_has_permission(
    admin_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=admin_user)
    mock_view = mock.MagicMock(detail=False, kwargs={"project_pk": project.id})
    actions = ["list", "create"]
    permissions = IsProjectAdmin()

    # When
    results = []
    for action in actions:
        mock_view.action = action
        results.append(permissions.has_permission(mock_request, mock_view))  # type: ignore[no-untyped-call]

    # Then
    assert all(results)


def test_organisation_admin_has_object_permission(
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
    organisation: Organisation,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    # From refactoring: It is unclear why the original test needs
    # to include the below permission check.
    upp = with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=admin_user)
    mock_view = mock.MagicMock(detail=False, kwargs={"project_pk": project.id})
    actions = ["update", "destroy"]
    permissions = IsProjectAdmin()

    # When
    results = []
    for action in actions:
        mock_view.action = action
        results.append(permissions.has_object_permission(mock_request, mock_view, upp))  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert all(results)


def test_regular_user_has_no_list_permission(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="list", detail=False, kwargs={"project_pk": project.id}
    )
    permissions = IsProjectAdmin()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_regular_user_has_no_create_permission(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="create", detail=False, kwargs={"project_pk": project.id}
    )
    permissions = IsProjectAdmin()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_regular_user_has_no_update_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    upp = with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="update", detail=True, kwargs={"project_pk": project.id}
    )
    permissions = IsProjectAdmin()

    # When
    result = permissions.has_object_permission(mock_request, mock_view, upp)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_regular_user_has_no_destroy_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    upp = with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="destroy", detail=True, kwargs={"project_pk": project.id}
    )
    permissions = IsProjectAdmin()

    # When
    result = permissions.has_object_permission(mock_request, mock_view, upp)  # type: ignore[no-untyped-call]

    # Then - exception thrown
    assert not result


@pytest.mark.django_db
def test_free_plan_has_only_fixed_projects_permission() -> None:
    # Given
    organisation = Organisation.objects.create(name="Test organisation")

    user = FFAdminUser.objects.create(email="admin@test.com")

    user.add_organisation(organisation, OrganisationRole.ADMIN)

    project_permissions = ProjectPermissions()

    mock_view = mock.MagicMock(action="create", detail=False)
    mock_request = mock.MagicMock(
        data={"name": "Test", "organisation": organisation.id}, user=user
    )

    # When
    for i in range(settings.MAX_PROJECTS_IN_FREE_PLAN):
        assert project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]
        Project.objects.create(name=f"Test project{i}", organisation=organisation)

    # Then - free projects limit should be exhausted
    assert not project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission_raises_permission_denied_if_not_found(  # type: ignore[no-untyped-def]
    mocker, admin_user
) -> None:
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": 1})

    # Then
    with pytest.raises(PermissionDenied):
        IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission_raises_api_exception_if_no_kwarg(  # type: ignore[no-untyped-def]
    mocker, admin_user
) -> None:
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"foo": "bar"})

    # Then
    with pytest.raises(APIException):
        IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission_returns_true_if_project_admin(  # type: ignore[no-untyped-def]
    mocker, admin_user, organisation, project
) -> None:
    # Given
    assert admin_user.is_project_admin(project)
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": project.id})

    # Then
    assert IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]
