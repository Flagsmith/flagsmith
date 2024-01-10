from unittest import mock
from unittest.mock import MagicMock

import pytest

from features.models import Feature
from features.permissions import FeaturePermissions
from organisations.models import Organisation
from permissions.models import PermissionModel
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import (
    CREATE_FEATURE,
    DELETE_FEATURE,
    VIEW_PROJECT,
    NestedProjectPermissions,
)
from tests.types import WithProjectPermissionsCallable
from users.models import FFAdminUser, UserPermissionGroup


def test_organisation_admin_can_list_features(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={"project_pk": project.id},
        detail=False,
        action="list",
    )
    mock_request = mock.MagicMock(data={}, user=admin_user)

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_admin_can_list_features(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={"project_pk": project.id},
        detail=False,
        action="list",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)
    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_with_read_access_can_list_features(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    with_project_permissions([VIEW_PROJECT])
    mock_view = mock.MagicMock(
        kwargs={"project_pk": project.id},
        detail=False,
        action="list",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_user_with_no_project_permissions_cannot_list_features(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={"project_pk": project.id},
        detail=False,
        action="list",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_organisation_admin_can_create_feature(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=False,
        action="create",
    )
    mock_request = mock.MagicMock(
        data={"project": project.id, "name": "new feature"}, user=admin_user
    )

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_admin_can_create_feature(
    organisation: Organisation,
    project: Project,
    staff_user: FFAdminUser,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    # use a group to test groups work too
    group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    UserPermissionGroupProjectPermission.objects.create(
        group=group, project=project, admin=True
    )
    group.users.add(staff_user)

    mock_view = mock.MagicMock(
        kwargs={},
        detail=False,
        action="create",
    )
    mock_request = mock.MagicMock(
        data={"project": project.id, "name": "new feature"}, user=staff_user
    )

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_with_create_feature_permission_can_create_feature(
    staff_user: FFAdminUser,
    project: Project,
    organisation: Organisation,
) -> None:
    # Given
    # use a group to test groups work too
    group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    group.users.add(staff_user)
    user_group_permission = UserPermissionGroupProjectPermission.objects.create(
        group=group, project=project, admin=False
    )
    user_group_permission.add_permission(CREATE_FEATURE)
    feature_permissions = FeaturePermissions()

    mock_view = mock.MagicMock(
        kwargs={},
        detail=False,
        action="create",
    )
    mock_request = mock.MagicMock(
        data={"project": project.id, "name": "new feature"}, user=staff_user
    )

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_without_create_feature_permission_cannot_create_feature(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=False,
        action="create",
    )
    mock_request = mock.MagicMock(
        data={"project": project.id, "name": "new feature"}, user=staff_user
    )

    # When
    result = feature_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_organisation_admin_can_view_feature(
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=True,
        action="retrieve",
    )
    mock_request = mock.MagicMock(data={}, user=admin_user)
    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_admin_can_view_feature(
    staff_user: FFAdminUser,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=True,
        action="retrieve",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)
    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_user_with_view_project_permission_can_view_feature(
    staff_user: FFAdminUser,
    project: Project,
    with_project_permissions: WithProjectPermissionsCallable,
    feature: Feature,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=True,
        action="retrieve",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_user_without_view_project_permission_cannot_view_feature(
    staff_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=True,
        action="retrieve",
    )
    mock_request = mock.MagicMock(data={}, user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is False


@pytest.mark.parametrize("action", (("update"), ("partial_update")))
def test_organisation_admin_can_edit_feature(
    action: str,
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(
        kwargs={},
        detail=True,
        action=action,
    )
    mock_request = mock.MagicMock(data={}, user=admin_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


@pytest.mark.parametrize("action", (("update"), ("partial_update")))
def test_project_admin_can_edit_feature(
    action: str,
    staff_user: FFAdminUser,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action=action)
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


@pytest.mark.parametrize("action", (("update"), ("partial_update")))
def test_project_user_cannot_edit_feature(
    action: str,
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action=action)
    mock_request = mock.MagicMock(user=staff_user)

    # User can only view the project, not edit features.
    with_project_permissions([VIEW_PROJECT])

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is False


def test_organisation_admin_can_delete_feature(
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="destroy")
    mock_request = mock.MagicMock(user=admin_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_admin_can_delete_feature(
    staff_user: FFAdminUser,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="destroy")
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_user_with_delete_feature_permission_can_delete_feature(
    staff_user: FFAdminUser,
    with_project_permissions: WithProjectPermissionsCallable,
    feature: Feature,
) -> None:
    # Given
    with_project_permissions([DELETE_FEATURE])

    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="destroy")
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_user_without_delete_feature_permission_cannot_delete_feature(
    staff_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="destroy")
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is False


def test_organisation_admin_can_update_feature_segments(
    admin_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="segments")
    mock_request = mock.MagicMock(user=admin_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_admin_can_update_feature_segments(
    staff_user: FFAdminUser,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="segments")
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is True


def test_project_user_cannot_update_feature_segments(
    staff_user: FFAdminUser,
    feature: Feature,
) -> None:
    # Given
    feature_permissions = FeaturePermissions()
    mock_view = mock.MagicMock(detail=True, action="segments")
    mock_request = mock.MagicMock(user=staff_user)

    # When
    result = feature_permissions.has_object_permission(mock_request, mock_view, feature)

    # Then
    assert result is False


@pytest.mark.parametrize(
    "action_permission_map, action, user_permission, expected_result",
    (
        ({}, "list", None, False),
        ({}, "list", VIEW_PROJECT, True),
        ({"create": CREATE_FEATURE}, "create", None, False),
        ({"create": CREATE_FEATURE}, "create", CREATE_FEATURE, True),
    ),
)
def test_nested_project_permissions_has_permission(
    action_permission_map,
    action,
    user_permission,
    expected_result,
    project,
    django_user_model,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation)

    if user_permission:
        permission_model = PermissionModel.objects.get(key=user_permission)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=project, admin=False
        )
        user_project_permission.permissions.add(permission_model)

    permission_class = NestedProjectPermissions(
        action_permission_map=action_permission_map
    )

    request = MagicMock(user=user)
    view = MagicMock(action=action, kwargs={"project_pk": project.id})

    # When
    result = permission_class.has_permission(request, view)

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "action_permission_map, action, user_permission, expected_result",
    (
        ({}, "list", None, False),
        ({}, "list", VIEW_PROJECT, True),
        ({"update": CREATE_FEATURE}, "update", None, False),
        ({"update": CREATE_FEATURE}, "update", CREATE_FEATURE, True),
    ),
)
def test_nested_project_permissions_has_object_permission(
    action_permission_map,
    action,
    user_permission,
    expected_result,
    project,
    django_user_model,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation)

    if user_permission:
        permission_model = PermissionModel.objects.get(key=user_permission)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=project, admin=False
        )
        user_project_permission.permissions.add(permission_model)

    permission_class = NestedProjectPermissions(
        action_permission_map=action_permission_map
    )

    request = MagicMock(user=user)
    view = MagicMock(action=action, kwargs={"project_pk": project.id})

    obj = MagicMock(project=project)

    # When
    result = permission_class.has_object_permission(request, view, obj)

    # Then
    assert result == expected_result
