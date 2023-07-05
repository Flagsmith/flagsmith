from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
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
