import uuid
from unittest import mock

from environments.identities.models import Identity
from environments.models import Environment
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.permissions import VIEW_PROJECT
from segments.models import Segment
from segments.permissions import SegmentPermissions
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

segment_permissions = SegmentPermissions()


def test_staff_user_has_permission(staff_user: FFAdminUser, project: Project) -> None:
    # Given
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    segment_permissions = SegmentPermissions()

    # When
    results = []
    for action in ("list", "create"):
        mock_view.action = action
        results.append(segment_permissions.has_permission(mock_request, mock_view))

    # Then
    assert all(results)


def test_project_admin_has_object_permission(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
    segment: Segment,
) -> None:
    # Given
    with_project_permissions(admin=True)
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    segment_permissions = SegmentPermissions()

    # When
    results = []
    for action in ("update", "destroy", "retrieve"):
        mock_view.action = action
        results.append(
            segment_permissions.has_object_permission(mock_request, mock_view, segment)
        )

    # Then
    assert all(results)


def test_project_user_has_list_permission(
    project: Project,
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    mock_view.detail = False
    with_project_permissions([VIEW_PROJECT])
    segment_permissions = SegmentPermissions()

    # When
    mock_view.action = "list"
    result = segment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_has_no_create_permission(
    project: Project,
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    mock_view.detail = False
    with_project_permissions([VIEW_PROJECT])
    segment_permissions = SegmentPermissions()

    # When
    mock_view.action = "create"
    result = segment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_project_user_has_object_permission(
    project: Project,
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    segment: Segment,
) -> None:
    # Given
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    with_project_permissions([VIEW_PROJECT])
    segment_permissions = SegmentPermissions()

    # When
    for action, expected_result in (
        ("retrieve", True),
        ("destroy", False),
        ("update", False),
        ("partial_update", False),
    ):
        mock_view.action = action

        # Then
        assert (
            segment_permissions.has_object_permission(mock_request, mock_view, segment)
            == expected_result
        )


def test_environment_admin_can_get_segments_for_an_identity(
    project: Project,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    segment: Segment,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    mock_request = mock.MagicMock()
    mock_request.user = staff_user
    mock_request.query_params = {}
    mock_view = mock.MagicMock()
    mock_view.kwargs = {"project_pk": project.id}
    with_environment_permissions(admin=True)
    identity = Identity.objects.create(identifier="test", environment=environment)
    mock_request.query_params["identity"] = identity.id
    segment_permissions = SegmentPermissions()

    # When
    result = segment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result


def test_user_with_view_project_permission_can_list_segments_for_an_identity(
    segment, django_user_model, mocker
):
    # Given
    permissions = SegmentPermissions()
    identity_uuid = uuid.uuid4()

    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(segment.project.organisation)

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=segment.project
    )
    user_project_permission.permissions.add(
        PermissionModel.objects.get(key=VIEW_PROJECT)
    )

    request = mocker.MagicMock(user=user, query_params={"identity": identity_uuid})
    view = mocker.MagicMock(action="list", kwargs={"project_pk": segment.project_id})

    # When
    result = permissions.has_permission(request, view)

    # Then
    assert result
