import typing

import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from environments.models import Environment
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from permissions.permission_service import is_user_environment_admin
from projects.models import UserPermissionGroupProjectPermission, UserProjectPermission
from users.models import FFAdminUser


def test_is_user_environment_admin_returns_true_for_org_admin(admin_user, environment):  # type: ignore[no-untyped-def]  # noqa: E501
    assert is_user_environment_admin(admin_user, environment) is True


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin_returns_true_for_project_admin(
    staff_user: FFAdminUser,
    environment: Environment,
    project_admin: typing.Union[
        UserProjectPermission, UserPermissionGroupProjectPermission
    ],
) -> None:
    # Then
    assert is_user_environment_admin(staff_user, environment) is True


@pytest.mark.parametrize(
    "environment_admin",
    [
        (lazy_fixture("environment_admin_via_user_permission")),
        (lazy_fixture("environment_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin_returns_true_for_environment_admin(  # type: ignore[no-untyped-def]
    staff_user: FFAdminUser,
    environment: Environment,
    environment_admin: typing.Union[
        UserEnvironmentPermission, UserPermissionGroupEnvironmentPermission
    ],
):
    # Then
    assert is_user_environment_admin(staff_user, environment) is True


def test_is_user_environment_admin_returns_false_for_user_with_no_permission(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    assert is_user_environment_admin(staff_user, environment) is False


def test_is_user_environment_admin_returns_false_for_user_with_admin_permission_of_other_org(  # type: ignore[no-untyped-def]  # noqa: E501
    admin_user,
    organisation_two_project_one_environment_one,
):
    assert (
        is_user_environment_admin(
            admin_user, organisation_two_project_one_environment_one
        )
        is False
    )


def test_is_user_environment_admin_returns_false_for_user_with_admin_permission_of_other_environment(  # type: ignore[no-untyped-def]  # noqa: E501
    django_user_model,
    environment,
    user_project_permission,
    user_environment_permission,
    user_project_permission_group,
    user_environment_permission_group,
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    # First, let's give the user admin permission
    user_project_permission.admin = True
    user_project_permission.save()

    user_environment_permission.admin = True
    user_environment_permission.save()

    # let's give the user admin permission using a group
    user_project_permission_group.admin = True
    user_project_permission_group.save()

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    # Then - the user should not be admin of the environment
    assert is_user_environment_admin(user, environment) is False
