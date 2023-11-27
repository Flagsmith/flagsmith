import pytest
from django.conf import settings

from organisations.models import OrganisationRole
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from permissions.models import ORGANISATION_PERMISSION_TYPE


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migration_creates_create_project_permissions_for_org_users(migrator):
    # Given
    # we use one of the dependencies of the migration we want to test to set the
    # initial state of the database correctly
    old_state = migrator.apply_initial_migration(
        ("organisations", "0027_organisation_restrict_project_create_to_admin")
    )
    old_ff_admin_user_model_class = old_state.apps.get_model("users", "FFAdminUser")
    old_organisation_model_class = old_state.apps.get_model(
        "organisations", "Organisation"
    )
    old_user_organisation_model_class = old_state.apps.get_model(
        "organisations", "UserOrganisation"
    )

    # a basic organisation
    organisation = old_organisation_model_class.objects.create(name="Test Org")

    # a regular user that belongs to the organisation and has
    # the organisation role 'USER'
    regular_user = old_ff_admin_user_model_class.objects.create(
        email="regular_user@testorg.com"
    )
    old_user_organisation_model_class.objects.create(
        user=regular_user, organisation=organisation, role=OrganisationRole.USER.name
    )

    # and an admin user of the organisation
    admin_user = old_ff_admin_user_model_class.objects.create(email="admin@testorg.com")
    old_user_organisation_model_class.objects.create(
        user=admin_user, organisation=organisation, role=OrganisationRole.ADMIN.name
    )

    # When
    # we apply the migration we want to test
    new_state = migrator.apply_tested_migration(
        ("organisation_permissions", "0001_initial")
    )
    new_user_organisation_permission_model_class = new_state.apps.get_model(
        "organisation_permissions", "UserOrganisationPermission"
    )

    # Then
    # a new permission is created for the regular user
    assert new_user_organisation_permission_model_class.objects.filter(
        user__id=regular_user.id,
        organisation__id=organisation.id,
        permissions__key=CREATE_PROJECT,
    ).exists()
    # but not for the admin user
    assert not new_user_organisation_permission_model_class.objects.filter(
        user__id=admin_user.id,
        organisation__id=organisation.id,
        permissions__key=CREATE_PROJECT,
    ).exists()


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_merge_duplicate_permissions_migration(migrator):
    # Given - the migration state is at 0002 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("organisation_permissions", "0002_add_related_query_name")
    )
    # fetch model classes we are going to use
    Organisation = old_state.apps.get_model("organisations", "Organisation")

    UserModel = old_state.apps.get_model("users", "FFAdminUser")
    UserPermissionGroup = old_state.apps.get_model("users", "UserPermissionGroup")
    PermissionModel = old_state.apps.get_model("permissions", "PermissionModel")

    UserOrganisationPermission = old_state.apps.get_model(
        "organisation_permissions", "UserOrganisationPermission"
    )
    UserPermissionGroupOrganisationPermission = old_state.apps.get_model(
        "organisation_permissions", "UserPermissionGroupOrganisationPermission"
    )

    # Next, create some setup data
    PermissionModel.objects.create(
        key=MANAGE_USER_GROUPS,
        type=ORGANISATION_PERMISSION_TYPE,
        description="Allows the user to manage the groups in the organisation and their members.",
    )

    organisation = Organisation.objects.create(name="Test Organisation")

    test_user = UserModel.objects.create(email="test_user@mail.com")
    admin_user = UserModel.objects.create(email="admin_user@mail.com")

    user_permission_group = UserPermissionGroup.objects.create(
        name="Test User Permission Group", organisation=organisation
    )
    non_duplicate_permission = UserOrganisationPermission.objects.create(
        user=admin_user, organisation=organisation
    )

    # Now - Let's create duplicate permissions
    first_permission = UserOrganisationPermission.objects.create(
        user=test_user, organisation=organisation
    )
    first_permission.permissions.add(CREATE_PROJECT)

    second_permission = UserOrganisationPermission.objects.create(
        user=test_user, organisation=organisation
    )
    second_permission.permissions.add(CREATE_PROJECT)
    second_permission.permissions.add(MANAGE_USER_GROUPS)

    # Next, let's create duplicate permissions using a group
    first_group_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    first_group_permission.permissions.add(CREATE_PROJECT)

    second_group_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=user_permission_group, organisation=organisation
    )
    second_group_permission.permissions.add(CREATE_PROJECT)
    second_group_permission.permissions.add(MANAGE_USER_GROUPS)

    # When - we run the migration
    new_state = migrator.apply_tested_migration(
        ("organisation_permissions", "0003_merge_duplicate_permissions")
    )
    NewUserOrganisationPermission = new_state.apps.get_model(
        "organisation_permissions", "UserOrganisationPermission"
    )
    NewUserPermissionGroupOrganisationPermission = new_state.apps.get_model(
        "organisation_permissions", "UserPermissionGroupOrganisationPermission"
    )

    # Then - we expect the duplicate permissions to be merged
    merged_permission = NewUserOrganisationPermission.objects.get(
        user_id=test_user.id, organisation_id=organisation.id
    )
    assert {MANAGE_USER_GROUPS, CREATE_PROJECT} == set(
        merged_permission.permissions.values_list("key", flat=True)
    )

    merged_group_permission = NewUserPermissionGroupOrganisationPermission.objects.get(
        group=user_permission_group.id, organisation_id=organisation.id
    )
    assert {MANAGE_USER_GROUPS, CREATE_PROJECT} == set(
        merged_group_permission.permissions.values_list("key", flat=True)
    )

    # and non_duplicate permission still exists
    assert UserOrganisationPermission.objects.filter(
        id=non_duplicate_permission.id
    ).exists()
