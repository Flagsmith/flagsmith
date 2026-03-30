from unittest import mock

from common.projects.permissions import (
    MANAGE_TAGS,
    VIEW_PROJECT,
)

from projects.models import Project
from projects.tags.models import Tag
from projects.tags.permissions import TagPermissions
from tests.types import WithProjectPermissionsCallable
from users.models import FFAdminUser

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

permissions = TagPermissions()


def test_tag_permissions__project_admin_list_and_create__returns_true(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(kwargs={"project_pk": project.id})
    permissions = TagPermissions()

    # When
    results = []
    for action in ["list", "create"]:
        mock_view.action = action
        results.append(permissions.has_permission(mock_request, mock_view))  # type: ignore[no-untyped-call]

    # Then
    assert all(results)


def test_tag_permissions__project_admin_object_actions__returns_true(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(kwargs={"project_pk": project.id})
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)
    # When
    results = []
    for action in ["update", "delete", "detail"]:
        mock_view.action = action
        results.append(permissions.has_object_permission(mock_request, mock_view, tag))  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert all(results)


def test_tag_permissions__project_user_list_action__returns_true(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions(admin=True)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        detail=False,
        action="list",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_tag_permissions__project_user_without_manage_tags_create__returns_false(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT], admin=False)  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        detail=False,
        action="create",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_tag_permissions__project_user_update_or_delete__returns_false(
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
        results.append(permissions.has_object_permission(mock_request, mock_view, tag))  # type: ignore[no-untyped-call]  # noqa: E501

    # Then
    assert all(result is False for result in results)


def test_tag_permissions__project_user_detail_action__returns_true(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="detail",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)

    # When
    result = permissions.has_object_permission(mock_request, mock_view, tag)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_tag_permissions__project_user_with_manage_tags_create__returns_true(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT, MANAGE_TAGS])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="create",
        kwargs={"project_pk": project.id},
        detail=False,
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_tag_permissions__project_user_with_view_only_create__returns_false(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="create",
        kwargs={"project_pk": project.id},
        detail=False,
    )
    permissions = TagPermissions()

    # When
    result = permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_tag_permissions__project_user_with_manage_tags_detail__returns_true(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT, MANAGE_TAGS])  # type: ignore[call-arg]
    mock_request = mock.MagicMock(user=staff_user)
    mock_view = mock.MagicMock(
        action="detail",
        kwargs={"project_pk": project.id},
    )
    permissions = TagPermissions()
    tag = Tag.objects.create(label="test", project=project)

    # When
    result = permissions.has_object_permission(mock_request, mock_view, tag)  # type: ignore[no-untyped-call]

    # Then
    assert result is True
