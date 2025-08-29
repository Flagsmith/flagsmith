from django.test import RequestFactory
from pytest_mock import MockerFixture

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from environments.permissions.permissions import NestedEnvironmentPermissions
from permissions.models import ENVIRONMENT_PERMISSION_TYPE, PermissionModel
from users.models import FFAdminUser


def test_nested_environment_permissions_has_permission_false_if_no_env_key(  # type: ignore[no-untyped-def]
    rf, mocker, db
):
    # Given
    permissions = NestedEnvironmentPermissions()

    request = rf.get("/")
    view = mocker.MagicMock(action="retrieve", kwargs={})

    # When
    result = permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_nested_environment_permissions_has_permission_true_if_action_in_map(
    rf: RequestFactory,
    mocker: MockerFixture,
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
) -> None:
    # Given
    permission_key = "SOME_PERMISSION"
    permission = PermissionModel.objects.create(
        key=permission_key, type=ENVIRONMENT_PERMISSION_TYPE, description="foobar"
    )
    user_environment_permission.permissions.add(permission)

    action = "retrieve"
    permissions = NestedEnvironmentPermissions(
        action_permission_map={action: permission.key}
    )

    request = rf.get("/")
    request.user = staff_user
    view = mocker.MagicMock(
        action=action, kwargs={"environment_api_key": environment.api_key}
    )

    # When
    has_permission = permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert has_permission is True


def test_nested_environment_permissions_has_permission_if_create_and_user_is_admin(
    rf: RequestFactory,
    mocker: MockerFixture,
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
) -> None:
    # Given
    permissions = NestedEnvironmentPermissions()

    user_environment_permission.admin = True
    user_environment_permission.save()

    request = rf.get("/")
    request.user = staff_user
    view = mocker.MagicMock(
        action="create", kwargs={"environment_api_key": environment.api_key}
    )

    # When
    has_permission = permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    assert has_permission is True


def test_nested_environment_permissions_has_object_permission_true_if_action_in_map(
    rf: RequestFactory,
    mocker: MockerFixture,
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
) -> None:
    # Given
    permission_key = "SOME_PERMISSION"
    permission = PermissionModel.objects.create(
        key=permission_key, type=ENVIRONMENT_PERMISSION_TYPE, description="foobar"
    )

    action = "retrieve"
    permissions = NestedEnvironmentPermissions(
        action_permission_map={action: permission.key}
    )

    user_environment_permission.permissions.add(permission)

    request = rf.get("/")
    request.user = staff_user
    view = mocker.MagicMock(
        action=action, kwargs={"environment_api_key": environment.api_key}
    )

    obj = mocker.MagicMock(environment=environment)

    # When
    has_object_permission = permissions.has_object_permission(request, view, obj)  # type: ignore[no-untyped-call]

    # Then
    assert has_object_permission is True


def test_nested_environment_permissions_has_object_permission_true_if_user_is_admin(
    rf: RequestFactory,
    mocker: MockerFixture,
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
) -> None:
    # Given
    permissions = NestedEnvironmentPermissions()

    user_environment_permission.admin = True
    user_environment_permission.save()

    request = rf.get("/")
    request.user = staff_user
    view = mocker.MagicMock(
        action="action", kwargs={"environment_api_key": environment.api_key}
    )

    obj = mocker.MagicMock(environment=environment)

    # When
    has_object_permission = permissions.has_object_permission(request, view, obj)  # type: ignore[no-untyped-call]

    # Then
    assert has_object_permission is True
