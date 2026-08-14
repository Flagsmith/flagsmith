import typing

import pytest
from django.conf import settings

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


def test_user_has_organisation_permission__no_permissions_assigned__returns_false(
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given / When
    # Then
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            user_has_organisation_permission(staff_user, organisation, permission)
            is False
        )


def test_user_has_organisation_permission__user_is_admin__returns_true(  # type: ignore[no-untyped-def]
    admin_user, organisation
):
    # Given / When
    # Then
    for permission in OrganisationPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            user_has_organisation_permission(admin_user, organisation, permission)
            is True
        )


def test_user_has_organisation_permission__permission_assigned_directly__returns_true(
    staff_user: FFAdminUser, organisation: Organisation
) -> None:
    # Given
    user_org_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_org_permission.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]
    user_org_permission.permissions.add(MANAGE_USER_GROUPS)  # type: ignore[arg-type]

    # When / Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission__permission_via_group__returns_true(
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

    # When / Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )

    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is False
    )


def test_user_has_organisation_permission__permission_via_group_and_directly__returns_true(
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

    # When / Then
    assert (
        user_has_organisation_permission(staff_user, organisation, CREATE_PROJECT)
        is True
    )
    assert (
        user_has_organisation_permission(staff_user, organisation, MANAGE_USER_GROUPS)
        is True
    )


def test_user_has_organisation_permission__user_removed_from_organisation__returns_false_for_orphan_group_permission(
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


def test_user_has_organisation_permission__direct_permission__short_circuits_in_three_queries(
    staff_user: FFAdminUser,
    organisation: Organisation,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given
    user_org_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_org_permission.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]

    # When
    # Should take only 3 queries:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership
    # 3. Check direct user permission (short-circuits here)
    with django_assert_num_queries(3):
        result = user_has_organisation_permission(
            staff_user, organisation, CREATE_PROJECT
        )

    # Then
    assert result is True


def test_user_has_organisation_permission__group_permission__short_circuits_in_four_queries(
    staff_user: FFAdminUser,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given
    user_permission_group.users.add(staff_user)
    group_org_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    group_org_permission.permissions.add(CREATE_PROJECT)  # type: ignore[arg-type]

    # When
    # Should take only 4 queries:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership
    # 3. Check direct user permission (not found)
    # 4. Check group permission (short-circuits here)
    with django_assert_num_queries(4):
        result = user_has_organisation_permission(
            staff_user, organisation, CREATE_PROJECT
        )

    # Then
    assert result is True


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is True,
    reason="Skip this test if RBAC is installed",
)
def test_user_has_organisation_permission__no_permissions_assigned__checks_each_source_in_four_queries(
    staff_user: FFAdminUser,
    organisation: Organisation,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    # Should take exactly 4 queries, one per permission source — never a
    # single combined query joining the user and group permission tables:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership
    # 3. Check direct user permission (not found)
    # 4. Check group permission (not found; role check skipped without RBAC)
    with django_assert_num_queries(4):
        result = user_has_organisation_permission(
            staff_user, organisation, MANAGE_USER_GROUPS
        )

    # Then
    assert result is False


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is False,
    reason="Skip this test if RBAC is not installed",
)
def test_user_has_organisation_permission__no_permissions_assigned_with_rbac__checks_each_source_in_five_queries(
    staff_user: FFAdminUser,
    organisation: Organisation,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    # Should take exactly 5 queries, one per permission source — never a
    # single combined query joining the user and group permission tables:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership
    # 3. Check direct user permission (not found)
    # 4. Check group permission (not found)
    # 5. Check role permission (not found)
    with django_assert_num_queries(5):
        result = user_has_organisation_permission(
            staff_user, organisation, MANAGE_USER_GROUPS
        )

    # Then
    assert result is False


def test_user_has_organisation_permission__user_not_in_organisation__short_circuits_in_two_queries(
    organisation: Organisation,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given
    user = FFAdminUser.objects.create(email="not-a-member@example.com")

    # When
    # Should take only 2 queries:
    # 1. Check if user is org admin (is_user_organisation_admin)
    # 2. Check organisation membership (short-circuits here)
    with django_assert_num_queries(2):
        result = user_has_organisation_permission(
            user, organisation, MANAGE_USER_GROUPS
        )

    # Then
    assert result is False
