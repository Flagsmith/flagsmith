from unittest import mock

from projects.models import Project
from projects.permissions import VIEW_PROJECT
from projects.tags.models import Tag
from projects.tags.permissions import TagPermissions
from tests.types import WithProjectPermissionsCallable
from users.models import FFAdminUser

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

permissions = TagPermissions()


def test_project_admin_has_permission(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(kwargs={"project_pk": project.id})
    permissions = TagPermissions()

    # When
    results = []
    for action in ["list", "create"]:
        mock_view.action = action
        results.append(permissions.has_permission(mock_request, mock_view))

    # Then
    assert all(results)


def test_project_admin_has_object_permission(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(kwargs={"project_pk": project.id})
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)
    # When
    results = []
    for action in ["update", "delete", "detail"]:
        mock_view.action = action
        results.append(permissions.has_object_permission(mock_request, mock_view, tag))

    # Then
    assert all(results)


def test_project_user_has_list_permission(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        detail=False,
        action="list",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_has_no_create_permission(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT], admin=False)
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        detail=False,
        action="create",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_project_user_has_no_update_or_delete_permission(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        detail=False,
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)

    # When
    results = []
    for action in ["update", "delete"]:
        mock_view.action = action
        results.append(permissions.has_object_permission(mock_request, mock_view, tag))

    # Then
    assert all(result is False for result in results)


def test_project_user_has_detail_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="detail",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)

    # When
    result = permissions.has_object_permission(mock_request, mock_view, tag)

    # Then
    assert result is True
