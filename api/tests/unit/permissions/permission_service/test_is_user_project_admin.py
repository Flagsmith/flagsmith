import pytest
from pytest_lazyfixture import lazy_fixture

from organisations.roles.models import RoleProjectPermission, UserRole
from permissions.permission_service import is_user_project_admin


def test_is_user_project_admin_returns_true_for_org_admin(
    organisation, admin_user, project
):
    assert is_user_project_admin(admin_user, project) is True


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
        (lazy_fixture("project_admin_via_user_role")),
        (lazy_fixture("project_admin_via_group_role")),
    ],
)
def test_is_user_project_admin_returns_true_for_project_admin(
    organisation,
    test_user,
    project,
    project_admin,
):
    # Then
    assert is_user_project_admin(test_user, project) is True


def test_is_user_project_admin_returns_false_for_user_with_no_permission(
    organisation,
    test_user,
    project,
):
    assert is_user_project_admin(test_user, project) is False


def test_is_user_project_admin_returns_false_for_user_with_admin_permission_of_other_org(
    admin_user,
    project,
    organisation_two_project_one,
):
    assert is_user_project_admin(admin_user, organisation_two_project_one) is False


def test_is_user_project_admin_returns_false_for_user_with_incorrect_permission(
    admin_user,
    project,
    organisation,
    user_project_permission,
    role,
    user_project_permission_group,
    group_role,
    organisation_two_project_one,
):
    # Given
    # let's give the user with admin permission on the project
    user_project_permission.admin = True
    user_project_permission.save()

    # let's give the user admin permission using a group
    user_project_permission_group.admin = True
    user_project_permission_group.save()

    # Next, let's give the user admin permission using a role
    UserRole.objects.create(user=admin_user, role=role)
    RoleProjectPermission.objects.create(role=role, project=project, admin=True)

    # Then - the user should not have admin permission on the other project
    assert is_user_project_admin(admin_user, organisation_two_project_one) is False
