from unittest import mock

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from environments.permissions.permissions import (
    EnvironmentAdminPermission,
    EnvironmentPermissions,
    NestedEnvironmentPermissions,
)
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserProjectPermission,
)
from projects.permissions import CREATE_ENVIRONMENT
from users.models import FFAdminUser

mock_view = mock.MagicMock()
mock_request = mock.MagicMock()

environment_permissions = EnvironmentPermissions()
nested_environment_permissions = NestedEnvironmentPermissions()
environment_admin_permissions = EnvironmentAdminPermission()


def test_environment_admin_permissions_has_permissions_returns_false_for_non_admin_user(
    environment, django_user_model, mocker
) -> None:
    # Given
    user = django_user_model.objects.create(username="test_user")
    mocked_request = mocker.MagicMock()
    mocked_request.user = user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    has_permission = environment_admin_permissions.has_permission(
        mocked_request, mocked_view
    )
    assert has_permission is False


def test_environment_admin_permissions_has_permissions_returns_true_for_admin_user(
    environment, django_user_model, mocker
) -> None:
    # Given
    user = django_user_model.objects.create(username="test_user")
    UserEnvironmentPermission.objects.create(
        user=user, environment=environment, admin=True
    )
    mocked_request = mocker.MagicMock()
    mocked_request.user = user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    has_permission = environment_admin_permissions.has_permission(
        mocked_request, mocked_view
    )
    assert has_permission is True


def test_org_admin_can_create_environment_for_any_project(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_admin_can_create_environment_in_project(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_with_create_environment_permission_can_create_environment(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    create_environment_permission = ProjectPermissionModel.objects.get(
        key=CREATE_ENVIRONMENT
    )
    user_project_permission = UserProjectPermission.objects.create(
        user=staff_user, project=project
    )
    user_project_permission.permissions.set([create_environment_permission])
    mock_request.user = staff_user
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_project_user_without_create_environment_permission_cannot_create_environment(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request.user = staff_user
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_all_users_can_list_environments_for_project(
    staff_user: FFAdminUser,
) -> None:
    # Given
    mock_view.action = "list"
    mock_view.detail = False
    mock_request.user = staff_user

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_organisation_admin_can_delete_environment(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "delete"
    mock_view.detail = True
    mock_request.user = admin_user

    # When
    result = environment_permissions.has_object_permission(
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_project_admin_can_delete_environment(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_environment_admin_can_delete_environment(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_regular_user_cannot_delete_environment(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = staff_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(
        mock_request, mock_view, environment
    )

    # Then
    assert result is False


def test_organisation_admin_has_create_permission(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    result = nested_environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_environment_admin_has_create_permission(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    UserEnvironmentPermission.objects.create(
        user=staff_user, environment=environment, admin=True
    )
    mock_view.action = "create"
    mock_view.detail = False
    mock_view.kwargs = {"environment_api_key": environment.api_key}
    mock_request.user = staff_user

    # When
    result = nested_environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is True


def test_regular_user_does_not_have_create_permission(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = staff_user
    mock_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    result = nested_environment_permissions.has_permission(mock_request, mock_view)

    # Then
    assert result is False


def test_organisation_admin_has_destroy_permission(
    admin_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    mock_view.action = "destroy"
    mock_view.detail = True
    mock_request.user = admin_user

    # When
    result = nested_environment_permissions.has_object_permission(
        mock_request, mock_view, identity
    )

    # Then
    assert result is True


def test_environment_admin_has_destroy_permission(
    staff_user: FFAdminUser,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    UserEnvironmentPermission.objects.create(
        user=staff_user, environment=environment, admin=True
    )
    mock_view.action = "destroy"
    mock_view.detail = True
    mock_request.user = staff_user

    # When
    result = nested_environment_permissions.has_object_permission(
        mock_request, mock_view, identity
    )

    # Then
    assert result is True


def test_regular_user_does_not_have_destroy_permission(
    staff_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    mock_view.action = "destroy"
    mock_view.detail = True
    mock_request.user = staff_user

    # When
    result = nested_environment_permissions.has_object_permission(
        mock_request, mock_view, identity
    )

    # Then
    assert result is False
