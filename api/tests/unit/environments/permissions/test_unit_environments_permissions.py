from unittest import mock

import pytest
from common.projects.permissions import (
    CREATE_ENVIRONMENT,
)
from pytest_mock import MockerFixture
from rest_framework.exceptions import ValidationError

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
from users.models import FFAdminUser

mock_view = mock.MagicMock()
mock_request = mock.MagicMock()

environment_permissions = EnvironmentPermissions()
nested_environment_permissions = NestedEnvironmentPermissions()
environment_admin_permissions = EnvironmentAdminPermission()


def test_environment_admin_permissions__non_admin_user__returns_false(  # type: ignore[no-untyped-def]  # noqa: E501
    environment, django_user_model, mocker
) -> None:
    # Given
    user = django_user_model.objects.create(username="test_user")
    mocked_request = mocker.MagicMock()
    mocked_request.user = user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    has_permission = environment_admin_permissions.has_permission(  # type: ignore[no-untyped-call]
        mocked_request, mocked_view
    )

    # Then
    assert has_permission is False


def test_environment_admin_permissions__admin_user__returns_true(
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
    mocker: MockerFixture,
) -> None:
    # Given
    mocked_request = mocker.MagicMock()
    mocked_request.user = staff_user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    user_environment_permission.admin = True
    user_environment_permission.save()

    # When
    has_permission = environment_admin_permissions.has_permission(  # type: ignore[no-untyped-call]
        mocked_request, mocked_view
    )

    # Then
    assert has_permission is True


def test_environment_permissions__org_admin_creates_environment__returns_true(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__project_admin_creates_environment__returns_true(
    admin_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__user_with_create_permission__returns_true(
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
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__user_without_create_permission__returns_false(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    # Given
    mock_request.user = staff_user
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.data = {"project": project.id, "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


@pytest.mark.parametrize(
    "request_data, expected",
    [
        ({"project": "<Project ID>", "name": "Test environment"}, False),
        ({"name": "Test environment"}, False),
    ],
)
def test_environment_permissions__create_with_invalid_project__returns_false(
    staff_user: FFAdminUser,
    request_data: dict[str, str],
    expected: bool,
) -> None:
    # Given
    view = mock.MagicMock()
    request = mock.MagicMock()
    view.action = "create"
    view.detail = False
    request.user = staff_user
    request.data = request_data

    # When
    result = environment_permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert result is expected


def test_environment_permissions__create_with_string_integer_project__returns_true(
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
    view = mock.MagicMock()
    request = mock.MagicMock()
    view.action = "create"
    view.detail = False
    request.user = staff_user
    request.data = {"project": str(project.id), "name": "Test environment"}

    # When
    result = environment_permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__list_action__returns_true(
    staff_user: FFAdminUser,
) -> None:
    # Given
    mock_view.action = "list"
    mock_view.detail = False
    mock_request.user = staff_user

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__org_admin_deletes_environment__returns_true(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "delete"
    mock_view.detail = True
    mock_request.user = admin_user

    # When
    result = environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_environment_permissions__project_admin_deletes_environment__returns_true(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_environment_permissions__environment_admin_deletes_environment__returns_true(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = admin_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_environment_permissions__regular_user_deletes_environment__returns_false(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_request.user = staff_user
    mock_view.action = "delete"
    mock_view.detail = True

    # When
    result = environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, environment
    )

    # Then
    assert result is False


def test_nested_environment_permissions__org_admin_creates__returns_true(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    result = nested_environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_nested_environment_permissions__environment_admin_creates__returns_true(
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
    result = nested_environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_nested_environment_permissions__regular_user_creates__returns_false(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given
    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = staff_user
    mock_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    result = nested_environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_nested_environment_permissions__org_admin_destroys__returns_true(
    admin_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    mock_view.action = "destroy"
    mock_view.detail = True
    mock_request.user = admin_user

    # When
    result = nested_environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, identity
    )

    # Then
    assert result is True


def test_nested_environment_permissions__environment_admin_destroys__returns_true(
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
    result = nested_environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, identity
    )

    # Then
    assert result is True


def test_nested_environment_permissions__regular_user_destroys__returns_false(
    staff_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    mock_view.action = "destroy"
    mock_view.detail = True
    mock_request.user = staff_user

    # When
    result = nested_environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, identity
    )

    # Then
    assert result is False


def test_environment_permissions__create_at_limit__raises_validation_error(
    admin_user: FFAdminUser,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_environments_allowed = 1
    project.save()

    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_request.data = {"project": project.id, "name": "Another environment"}
    mock_request.is_e2e = False

    # When / Then
    with pytest.raises(ValidationError, match="maximum number of allowed environments"):
        environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]


def test_environment_permissions__create_below_limit__returns_true(
    admin_user: FFAdminUser,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_environments_allowed = 100
    project.save()

    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_request.data = {"project": project.id, "name": "Another environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_environment_permissions__clone_at_limit__raises_validation_error(
    admin_user: FFAdminUser,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_environments_allowed = 1
    project.save()

    mock_view.action = "clone"
    mock_view.detail = True
    mock_request.user = admin_user
    mock_request.is_e2e = False

    # When / Then
    with pytest.raises(ValidationError, match="maximum number of allowed environments"):
        environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
            mock_request, mock_view, environment
        )


def test_environment_permissions__clone_below_limit__returns_true(
    admin_user: FFAdminUser,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_environments_allowed = 100
    project.save()

    mock_view.action = "clone"
    mock_view.detail = True
    mock_request.user = admin_user

    # When
    result = environment_permissions.has_object_permission(  # type: ignore[no-untyped-call]
        mock_request, mock_view, environment
    )

    # Then
    assert result is True


def test_environment_permissions__create_at_limit_with_increased_limit__returns_true(
    admin_user: FFAdminUser,
    project: Project,
    environment: Environment,
) -> None:
    """Grandfathering: projects with a higher limit can still create environments."""
    # Given
    project.max_environments_allowed = 200
    project.save()

    mock_view.action = "create"
    mock_view.detail = False
    mock_request.user = admin_user
    mock_request.data = {"project": project.id, "name": "Another environment"}

    # When
    result = environment_permissions.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True
