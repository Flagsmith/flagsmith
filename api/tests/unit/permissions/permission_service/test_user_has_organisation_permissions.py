from organisations.permissions.models import (
    OrganisationPermissionModel,
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
from permissions.permission_service import user_has_organisation_permission


def test_user_has_organisation_permission_returns_false_if_user_does_not_have_permission(
    test_user, organisation
):
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            user_has_organisation_permission(test_user, organisation, permission)
            is False
        )


def test_user_has_organisation_permission_returns_true_if_user_is_admin(
    admin_user, organisation
):
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            user_has_organisation_permission(admin_user, organisation, permission)
            is True
        )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_directly(
    test_user, organisation
):
    # Given
    user_org_permission = UserOrganisationPermission.objects.create(
        user=test_user, organisation=organisation
    )
    user_org_permission.permissions.add(CREATE_PROJECT)
    user_org_permission.permissions.add(MANAGE_USER_GROUPS)

    # Then
    assert (
        user_has_organisation_permission(test_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(test_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_via_group(
    test_user, organisation, user_permission_group
):
    # Given
    user_permission_group.users.add(test_user)
    user_perm_org_group = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    user_perm_org_group.permissions.add(CREATE_PROJECT)

    # Then
    assert (
        user_has_organisation_permission(test_user, organisation, CREATE_PROJECT)
        is True
    )

    assert (
        user_has_organisation_permission(test_user, organisation, MANAGE_USER_GROUPS)
        is False
    )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_via_group_and_directly(
    test_user, organisation, user_permission_group
):
    # Given
    user_permission_group.users.add(test_user)
    user_perm_org_group = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    user_perm_org_group.permissions.add(CREATE_PROJECT)

    user_org_permission = UserOrganisationPermission.objects.create(
        user=test_user, organisation=organisation
    )
    user_org_permission.permissions.add(MANAGE_USER_GROUPS)

    # Then
    assert (
        user_has_organisation_permission(test_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(test_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_via_roles(
    test_user,
    organisation,
    user_permission_group,
    user_role,
    create_project_permission,
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

    # Then
    assert (
        user_has_organisation_permission(test_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(test_user, organisation, MANAGE_USER_GROUPS)
        is True
    )
