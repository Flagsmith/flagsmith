from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from organisations.roles.models import (
    GroupRole,
    Role,
    RoleOrganisationPermission,
    UserRole,
)
from permissions.permission_service import (
    get_organisation_permission_keys_for_user,
)


def test_get_organisation_permission_keys_for_user_using_user_and_group(
    test_user,
    organisation,
    create_project_permission,
    user_permission_group,
    manage_user_group_permission,
):
    # Given
    # a user with create_project_permission(directly)
    user_org_permission = UserOrganisationPermission.objects.create(
        user=test_user, organisation=organisation
    )
    user_org_permission.permissions.add(create_project_permission)

    # and manager_user_group_permission(through group)
    user_permission_group.users.add(test_user)
    user_org_permission_group = (
        UserPermissionGroupOrganisationPermission.objects.create(
            group=user_permission_group, organisation=organisation
        )
    )
    user_org_permission_group.permissions.add(manage_user_group_permission)

    # When
    permission_keys = get_organisation_permission_keys_for_user(test_user, organisation)

    # Then
    assert permission_keys == {CREATE_PROJECT, MANAGE_USER_GROUPS}


def test_get_organisation_permission_keys_for_user_using_roles(
    test_user,
    organisation,
    create_project_permission,
    role_organisation_permission,
    user_role,
    role,
    group_role,
    user_permission_group,
    manage_user_group_permission,
):
    # Given
    # First, let's create a role for `create_project`
    create_project_role = Role.objects.create(
        organisation=organisation, name="Create project role"
    )
    create_project_role_permission = RoleOrganisationPermission.objects.create(
        role=create_project_role
    )
    create_project_role_permission.permissions.add(create_project_permission)

    # Next, let's crate another role for `manage_user_group`
    manage_user_group_role = Role.objects.create(
        organisation=organisation, name="Create project role"
    )
    manage_user_group_role_permission = RoleOrganisationPermission.objects.create(
        role=manage_user_group_role
    )
    manage_user_group_role_permission.permissions.add(manage_user_group_permission)
    user_permission_group.users.add(test_user)

    # Next, let's assign one role directly and assign the other using the user_permission_group
    UserRole.objects.create(user=test_user, role=create_project_role)
    GroupRole.objects.create(role=manage_user_group_role, group=user_permission_group)

    # When
    permission_keys = get_organisation_permission_keys_for_user(test_user, organisation)

    # Then
    assert permission_keys == {CREATE_PROJECT, MANAGE_USER_GROUPS}


def test_get_organisation_permission_keys_returns_empty_set_if_no_permisson_exists(
    test_user, organisation, user_permission_group, role, user_role, group_role
):
    # Given
    # let's create user org permission without attaching any permission to it
    UserOrganisationPermission.objects.create(user=test_user, organisation=organisation)

    # Next, let's do the same thing for group
    user_permission_group.users.add(test_user)
    UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )

    # and role(s) (with no permissions)
    RoleOrganisationPermission.objects.create(role=role)
    RoleOrganisationPermission.objects.create(role=role)

    # When
    permission_keys = get_organisation_permission_keys_for_user(test_user, organisation)

    # Then
    assert len(permission_keys) == 0
