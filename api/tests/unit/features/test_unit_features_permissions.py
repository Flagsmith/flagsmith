from unittest.mock import MagicMock

import pytest

from permissions.models import PermissionModel
from projects.models import UserProjectPermission
from projects.permissions import NestedProjectPermissions


@pytest.mark.parametrize(
    "action_permission_map, action, user_permission, expected_result",
    (
        ({}, "list", None, False),
        ({}, "list", "VIEW_PROJECT", True),
        ({"create": "CREATE_FEATURE"}, "create", None, False),
        ({"create": "CREATE_FEATURE"}, "create", "CREATE_FEATURE", True),
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
        ({}, "list", "VIEW_PROJECT", True),
        ({"update": "CREATE_FEATURE"}, "update", None, False),
        ({"update": "CREATE_FEATURE"}, "update", "CREATE_FEATURE", True),
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
