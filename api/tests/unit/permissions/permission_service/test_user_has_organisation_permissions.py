from organisations.models import Organisation, UserOrganisation
from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from permissions.models import PermissionModel
from permissions.permission_service import user_has_organisation_permission
from users.models import FFAdminUser, UserPermissionGroup


def test_user_has_organisation_permission_returns_false_if_user_does_not_have_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            user_has_organisation_permission(staff_user, organisation, permission)
            is False
        )


def test_user_has_organisation_permission_returns_true_if_user_is_admin(  # type: ignore[no-untyped-def]
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
    staff_user: FFAdminUser, organisation: Organisation
) -> None:
    # Given
    user_org_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_org_permission.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]
    user_org_permission.permissions.add(MANAGE_USER_GROUPS)  # type: ignore[arg-type]

    # Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_via_group(
    staff_user: FFAdminUser,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    user_permission_group.users.add(staff_user)
    user_perm_org_group = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    user_perm_org_group.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]

    # Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )

    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is False
    )


def test_user_has_organisation_permission_returns_true_if_user_has_permission_via_group_and_directly(
    staff_user: FFAdminUser,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    user_permission_group.users.add(staff_user)
    user_perm_org_group = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    user_perm_org_group.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]

    user_org_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_org_permission.permissions.add(MANAGE_USER_GROUPS)  # type: ignore[arg-type]

    # Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission__returns_false_for_orphan_group_permission(
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
    staff_user: FFAdminUser,
    create_project_permission: PermissionModel,
) -> None:
    """
    Specific test to verify that a user no longer has permission to access resources via a group,
    if they no longer belong to the organisation.

    Note that a user should never be a member of a group without being a member of the organisation
    but this test exists to ensure no security holes.
    """

    # Given
    staff_user.add_to_group(group=user_permission_group)

    group_organisation_permission = (
        UserPermissionGroupOrganisationPermission.objects.create(
            organisation=organisation, group=user_permission_group
        )
    )
    group_organisation_permission.permissions.add(create_project_permission)

    assert user_has_organisation_permission(
        user=staff_user,
        organisation=organisation,
        permission_key=CREATE_PROJECT,
    )

    # When
    # We delete the user organisation to remove the user from the organisation, without
    # allowing any signals / hooks to run.
    UserOrganisation.objects.filter(user=staff_user, organisation=organisation).delete()

    # Then
    assert not user_has_organisation_permission(
        user=staff_user,
        organisation=organisation,
        permission_key=CREATE_PROJECT,
    )
