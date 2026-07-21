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


def test_project_permissions_has_permission__staff_user_lists__returns_true(
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


def test_project_permissions_has_permission__user_with_create_permission__returns_true(
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


def test_project_permissions_has_permission__e2e_test_auth_token__returns_true(
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


def test_project_permissions_has_object_permission__project_admin_updates__returns_true(
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


def test_project_permissions_has_object_permission__admin_group_updates__returns_true(
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


def test_project_permissions_has_object_permission__regular_user_updates__returns_false(
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


def test_project_permissions_has_object_permission__admin_via_group_deletes__returns_true(
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


def test_project_permissions_has_object_permission__regular_user_deletes__returns_false(
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


def test_project_permissions__organisation_admin_all_actions__returns_true(
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


def test_project_permissions_has_object_permission__user_with_view_permission_retrieves__returns_true(
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


def test_is_project_admin_has_permission__project_admin_lists_and_creates__returns_true(
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


def test_is_project_admin_has_object_permission__project_admin_updates_and_deletes__returns_true(
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


def test_is_project_admin_has_permission__organisation_admin_lists_and_creates__returns_true(
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


def test_is_project_admin_has_object_permission__organisation_admin_updates_and_deletes__returns_true(
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


def test_is_project_admin_has_permission__regular_user_lists__returns_false(
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


def test_is_project_admin_has_permission__regular_user_creates__returns_false(
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


def test_is_project_admin_has_object_permission__regular_user_updates__returns_false(
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


def test_is_project_admin_has_object_permission__regular_user_deletes__returns_false(
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

    # Then
    assert not result


@pytest.mark.django_db
def test_project_permissions_has_permission__free_plan_exceeds_limit__returns_false() -> (
    None
):
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

    # Then
    assert not project_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission__project_not_found__raises_permission_denied(  # type: ignore[no-untyped-def]
    mocker, admin_user
) -> None:
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": 1})

    # When / Then
    with pytest.raises(PermissionDenied):
        IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission__missing_project_kwarg__raises_api_exception(  # type: ignore[no-untyped-def]
    mocker, admin_user
) -> None:
    # Given
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"foo": "bar"})

    # When / Then
    with pytest.raises(APIException):
        IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]


def test_is_project_admin_has_permission__user_is_project_admin__returns_true(  # type: ignore[no-untyped-def]
    mocker, admin_user, organisation, project
) -> None:
    # Given
    assert admin_user.is_project_admin(project)
    request = mocker.MagicMock(user=admin_user)
    view = mocker.MagicMock(kwargs={"project_pk": project.id})

    # When
    result = IsProjectAdmin().has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert result
