import typing

import pytest
from django.conf import settings
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from environments.models import Environment
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import Organisation, UserOrganisation
from permissions.permission_service import is_user_environment_admin
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


def test_is_user_environment_admin__org_admin__returns_true(admin_user, environment):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given / When
    # Then
    assert is_user_environment_admin(admin_user, environment) is True


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin__project_admin__returns_true(
    staff_user: FFAdminUser,
    environment: Environment,
    project_admin: typing.Union[
        UserProjectPermission, UserPermissionGroupProjectPermission
    ],
) -> None:
    # Given / When
    # Then
    assert is_user_environment_admin(staff_user, environment) is True


@pytest.mark.parametrize(
    "environment_admin",
    [
        (lazy_fixture("environment_admin_via_user_permission")),
        (lazy_fixture("environment_admin_via_user_permission_group")),
    ],
)
def test_is_user_environment_admin__environment_admin__returns_true(  # type: ignore[no-untyped-def]
    staff_user: FFAdminUser,
    environment: Environment,
    environment_admin: typing.Union[
        UserEnvironmentPermission, UserPermissionGroupEnvironmentPermission
    ],
):
    # Given / When
    # Then
    assert is_user_environment_admin(staff_user, environment) is True


def test_is_user_environment_admin__no_permission__returns_false(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given / When
    # Then
    assert is_user_environment_admin(staff_user, environment) is False


def test_is_user_environment_admin__admin_of_other_org__returns_false(  # type: ignore[no-untyped-def]
    admin_user,
    organisation_two_project_one_environment_one,
):
    # Given / When
    # Then
    assert (
        is_user_environment_admin(
            admin_user, organisation_two_project_one_environment_one
        )
        is False
    )


def test_is_user_environment_admin__admin_of_other_environment__returns_false(  # type: ignore[no-untyped-def]
    django_user_model,
    environment,
    user_project_permission,
    user_environment_permission,
    user_project_permission_group,
    user_environment_permission_group,
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    # When - give the user admin permission on other objects
    user_project_permission.admin = True
    user_project_permission.save()

    user_environment_permission.admin = True
    user_environment_permission.save()

    # let's give the user admin permission using a group
    user_project_permission_group.admin = True
    user_project_permission_group.save()

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    # Then
    assert is_user_environment_admin(user, environment) is False


def test_is_user_environment_admin__orphan_group_permission__returns_false(
    organisation: Organisation,
    project: Project,
    environment: Environment,
    user_permission_group: UserPermissionGroup,
    environment_permission_using_user_permission_group: UserPermissionGroupEnvironmentPermission,
    staff_user: FFAdminUser,
) -> None:
    """
    Specific test to verify that a user no longer has permission to access resources via a group,
    if they no longer belong to the organisation.

    Note that a user should never be a member of a group without being a member of the organisation
    but this test exists to ensure no security holes.
    """

    # Given
    environment_permission_using_user_permission_group.admin = True
    environment_permission_using_user_permission_group.save()

    assert is_user_environment_admin(user=staff_user, environment=environment)

    # When
    # We delete the user organisation to remove the user from the organisation, without
    # allowing any signals / hooks to run.
    UserOrganisation.objects.filter(user=staff_user, organisation=organisation).delete()

    # Then
    assert not is_user_environment_admin(user=staff_user, environment=environment)


def test_is_user_environment_admin__direct_permission__short_circuits_queries(
    staff_user: FFAdminUser,
    environment: Environment,
    environment_admin_via_user_permission: UserEnvironmentPermission,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    # Then should take only 6 queries (7 if RBAC installed):
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership for project (_is_user_object_admin)
    # 3. Check direct user permission on project (not found)
    # 4. Check group permission on project (not found)
    # 5. Check RBAC role permission on project (not found, only if RBAC installed)
    # 6. Check organisation membership for environment (_is_user_object_admin)
    # 7. Check direct user permission on environment (short-circuits here)
    expected_queries = 7 if settings.IS_RBAC_INSTALLED else 6
    with django_assert_num_queries(expected_queries):
        assert is_user_environment_admin(staff_user, environment) is True


def test_is_user_environment_admin__group_permission__short_circuits_queries(
    staff_user: FFAdminUser,
    environment: Environment,
    environment_admin_via_user_permission_group: UserPermissionGroupEnvironmentPermission,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    # Then should take only 7 queries (8 if RBAC installed):
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership for project (_is_user_object_admin)
    # 3. Check direct user permission on project (not found)
    # 4. Check group permission on project (not found)
    # 5. Check RBAC role permission on project (not found, only if RBAC installed)
    # 6. Check organisation membership for environment (_is_user_object_admin)
    # 7. Check direct user permission on environment (not found)
    # 8. Check group permission on environment (short-circuits here)
    expected_queries = 8 if settings.IS_RBAC_INSTALLED else 7
    with django_assert_num_queries(expected_queries):
        assert is_user_environment_admin(staff_user, environment) is True
