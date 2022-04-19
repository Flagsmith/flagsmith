from organisations.models import OrganisationRole


def test_migration_only_remove_permissions_for_users_that_are_not_part_of_the_organisation(
    migrator,
):
    # Given - the migration state is at 0004 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("permissions", "0004_add_create_project_permission"),
    )

    old_ff_admin_user_model_class = old_state.apps.get_model("users", "FFAdminUser")
    old_project_model_class = old_state.apps.get_model("projects", "Project")
    old_user_project_permission_model_class = old_state.apps.get_model(
        "projects", "UserProjectPermission"
    )
    old_environment_model_class = old_state.apps.get_model(
        "environments", "Environment"
    )
    old_user_environment_permission_model_class = old_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    old_organisation_model_class = old_state.apps.get_model(
        "organisations", "Organisation"
    )
    old_user_organisation_model_class = old_state.apps.get_model(
        "organisations", "UserOrganisation"
    )
    # Next, Create some test data
    organisation = old_organisation_model_class.objects.create(name="Test Org")

    # a user that belongs to the organisation
    member = old_ff_admin_user_model_class.objects.create(email="a_member@testorg.com")
    old_user_organisation_model_class.objects.create(
        user=member, organisation=organisation, role=OrganisationRole.USER.name
    )
    # and a user that is not member of the organisation
    not_a_member = old_ff_admin_user_model_class.objects.create(
        email="not_a_member@testorg.com"
    )
    project = old_project_model_class.objects.create(
        name="a_project", organisation=organisation
    )
    # create project user permission for both the users
    old_user_project_permission_model_class.objects.create(
        project=project, user=member, admin=True
    )
    old_user_project_permission_model_class.objects.create(
        project=project, user=not_a_member, admin=True
    )

    environment = old_environment_model_class.objects.create(
        name="an_environment", project=project
    )

    # create environment user permission for both the users
    old_user_environment_permission_model_class.objects.create(
        user=member, environment=environment, admin=True
    )
    old_user_environment_permission_model_class.objects.create(
        user=not_a_member, environment=environment, admin=True
    )

    # When - apply the migration
    new_state = migrator.apply_tested_migration(
        ("permissions", "0005_orphan_permission_cleanup")
    )

    # Update the state of all the models/objects
    new_user_project_permission_model_class = new_state.apps.get_model(
        "projects", "UserProjectPermission"
    )

    new_user_environment_permission_model_class = new_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )

    new_ff_admin_user_model_class = new_state.apps.get_model("users", "FFAdminUser")
    new_project_model_class = new_state.apps.get_model("projects", "Project")
    new_environment_model_class = new_state.apps.get_model(
        "environments", "Environment"
    )

    new_environment = new_environment_model_class.objects.get(id=environment.id)
    new_project = new_project_model_class.objects.get(id=project.id)

    new_member = new_ff_admin_user_model_class.objects.get(id=member.id)
    new_not_a_member = new_ff_admin_user_model_class.objects.get(id=not_a_member.id)
    # Finally - assert that project_user_permission is removed for not_a_member(but exists for member)
    assert (
        new_user_project_permission_model_class.objects.filter(
            project=new_project, user=new_member
        ).count()
        == 1
    )
    assert (
        new_user_project_permission_model_class.objects.filter(
            project=new_project, user=new_not_a_member
        ).count()
        == 0
    )

    # and,  environment_user_permission is removed for not_a_member(but exists for member)
    assert (
        new_user_environment_permission_model_class.objects.filter(
            environment=new_environment, user=new_member
        ).count()
        == 1
    )
    assert (
        new_user_environment_permission_model_class.objects.filter(
            environment=new_environment, user=new_not_a_member
        ).count()
        == 0
    )
