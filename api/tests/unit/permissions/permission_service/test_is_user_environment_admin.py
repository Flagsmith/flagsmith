from organisations.roles.models import (
    RoleEnvironmentPermission,
    RoleProjectPermission,
    UserRole,
)
from permissions.permission_service import is_user_environment_admin


def test_is_user_environment_admin_returns_true_for_org_admin(admin_user, environment):
    assert is_user_environment_admin(admin_user, environment) is True


def test_is_user_environment_admin_returns_true_for_project_admin_through_user(
    test_user, environment, user_project_permission
):
    # Given
    user_project_permission.admin = True
    user_project_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_envionment_admin_returns_for_project_admin_through_user_role(
    test_user, environment, role_project_permission, user_role
):
    # Given
    role_project_permission.admin = True
    role_project_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_true_for_project_admin_through_group_role(
    test_user, environment, role_project_permission, user_permission_group, group_role
):
    # Given
    user_permission_group.users.add(test_user)

    role_project_permission.admin = True
    role_project_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_true_for_project_admin_through_user_group(
    test_user, environment, user_project_permission_group, user_permission_group
):
    # Given
    user_permission_group.users.add(test_user)

    user_project_permission_group.admin = True
    user_project_permission_group.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_true_for_environment_admin_through_user(
    test_user, environment, user_environment_permission
):
    # Given
    user_environment_permission.admin = True
    user_environment_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_true_for_environment_admin_through_user_group(
    test_user, environment, user_environment_permission_group, user_permission_group
):
    # Given
    user_permission_group.users.add(test_user)

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_envionment_admin_returns_for_environment_admin_through_user_role(
    test_user, environment, role_environment_permission, user_role
):
    # Given
    role_environment_permission.admin = True
    role_environment_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_true_for_environment_admin_through_group_role(
    test_user,
    environment,
    role_environment_permission,
    user_permission_group,
    group_role,
):
    # Given
    user_permission_group.users.add(test_user)

    role_environment_permission.admin = True
    role_environment_permission.save()

    # Then
    assert is_user_environment_admin(test_user, environment) is True


def test_is_user_environment_admin_returns_false_for_user_with_no_permission(
    organisation,
    test_user,
    environment,
):
    assert is_user_environment_admin(test_user, environment) is False


def test_is_user_environment_admin_returns_false_for_user_with_admin_permission_of_other_org(
    admin_user,
    environment,
    other_environment,
):
    assert is_user_environment_admin(admin_user, other_environment) is False


def test_is_user_environment_admin_returns_false_for_user_with_incorrect_permission(
    admin_user,
    project,
    organisation,
    user_project_permission,
    user_environment_permission,
    role,
    user_project_permission_group,
    user_environment_permission_group,
    group_role,
    other_project,
    other_environment,
    environment,
):
    # Given
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

    # let's give the user admin permission using a role
    UserRole.objects.create(user=admin_user, role=role)

    RoleProjectPermission.objects.create(role=role, project=project, admin=True)

    RoleEnvironmentPermission.objects.create(
        role=role, environment=environment, admin=True
    )

    # Then - the user should not have admin permission on the other environment
    assert is_user_environment_admin(admin_user, other_environment) is False
