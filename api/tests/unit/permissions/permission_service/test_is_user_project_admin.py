import typing

import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from organisations.models import Organisation, UserOrganisation
from permissions.permission_service import is_user_project_admin
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


def test_is_user_project_admin_returns_true_for_org_admin(admin_user, project):  # type: ignore[no-untyped-def]
    assert is_user_project_admin(admin_user, project) is True


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_is_user_project_admin_returns_true_for_project_admin(
    staff_user: FFAdminUser,
    project: Project,
    project_admin: typing.Union[
        UserProjectPermission, UserPermissionGroupProjectPermission
    ],
) -> None:
    # Then
    assert is_user_project_admin(staff_user, project) is True


def test_is_user_project_admin_returns_false_for_user_with_no_permission(
    staff_user: FFAdminUser,
    project: Project,
) -> None:
    assert is_user_project_admin(staff_user, project) is False


def test_is_user_project_admin_returns_false_for_user_with_admin_permission_of_other_org(  # type: ignore[no-untyped-def]  # noqa: E501
    admin_user,
    organisation_two_project_one,
):
    assert is_user_project_admin(admin_user, organisation_two_project_one) is False


def test_is_user_project_admin_returns_false_for_user_with_incorrect_permission(  # type: ignore[no-untyped-def]
    admin_user,
    user_project_permission,
    user_project_permission_group,
    organisation_two_project_one,
):
    # Given
    # let's give the user with admin permission on the project
    user_project_permission.admin = True
    user_project_permission.save()

    # let's give the user admin permission using a group
    user_project_permission_group.admin = True
    user_project_permission_group.save()

    # Then - the user should not have admin permission on the other project
    assert is_user_project_admin(admin_user, organisation_two_project_one) is False


def test_is_user_project_admin__does_not_return_project_for_orphan_group_permission(
    organisation: Organisation,
    project: Project,
    user_permission_group: UserPermissionGroup,
    project_permission_using_user_permission_group: UserPermissionGroupProjectPermission,
    staff_user: FFAdminUser,
) -> None:
    """
    Specific test to verify that a user no longer has permission to access resources via a group,
    if they no longer belong to the organisation.

    Note that a user should never be a member of a group without being a member of the organisation
    but this test exists to ensure no security holes.
    """

    # Given
    project_permission_using_user_permission_group.admin = True
    project_permission_using_user_permission_group.save()

    assert is_user_project_admin(user=staff_user, project=project)

    # When
    # We delete the user organisation to remove the user from the organisation, without
    # allowing any signals / hooks to run.
    UserOrganisation.objects.filter(user=staff_user, organisation=organisation).delete()

    # Then
    assert not is_user_project_admin(user=staff_user, project=project)


def test_is_user_project_admin__short_circuits_on_direct_permission(
    staff_user: FFAdminUser,
    project: Project,
    project_admin_via_user_permission: UserProjectPermission,
    django_assert_num_queries: typing.Any,
) -> None:
    # When/Then - should take only 3 queries:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership (_is_user_object_admin)
    # 3. Check direct user permission (short-circuits here)
    with django_assert_num_queries(3):
        assert is_user_project_admin(staff_user, project) is True


def test_is_user_project_admin__short_circuits_on_group_permission(
    staff_user: FFAdminUser,
    project: Project,
    project_admin_via_user_permission_group: UserPermissionGroupProjectPermission,
    django_assert_num_queries: typing.Any,
) -> None:
    # When/Then - should take only 4 queries:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership (_is_user_object_admin)
    # 3. Check direct user permission (not found)
    # 4. Check group permission (short-circuits here)
    with django_assert_num_queries(4):
        assert is_user_project_admin(staff_user, project) is True
