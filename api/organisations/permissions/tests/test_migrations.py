from organisations.models import OrganisationRole
from organisations.permissions.permissions import CREATE_PROJECT


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
