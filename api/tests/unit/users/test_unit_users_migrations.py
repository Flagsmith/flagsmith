from django_test_migrations.migrator import Migrator


def test_remove_users_from_groups_in_orgs_the_do_not_belong_to(
    migrator: Migrator,
) -> None:
    # Given
    initial_state = migrator.apply_initial_migration(
        ("users", "0043_make_hubspot_cookie_optional")
    )

    user_class = initial_state.apps.get_model("users", "FFAdminUser")
    group_class = initial_state.apps.get_model("users", "UserPermissionGroup")
    organisation_class = initial_state.apps.get_model("organisations", "Organisation")
    user_organisation_class = initial_state.apps.get_model(
        "organisations", "UserOrganisation"
    )

    organisation = organisation_class.objects.create(
        name="Test Organisation",
    )

    user_1 = user_class.objects.create(email="test1@example.com")
    user_2 = user_class.objects.create(email="test2@example.com")

    # Add user_1 to the organisation, but not user 2
    user_organisation_class.objects.create(user=user_1, organisation=organisation)

    group = group_class.objects.create(name="Test Group", organisation=organisation)

    user_1.permission_groups.add(group)
    user_2.permission_groups.add(group)

    assert group.users.count() == 2

    # When
    migrator.apply_tested_migration(
        ("users", "0044_remove_users_from_groups_in_orgs_they_do_not_belong_to")
    )

    # Then
    assert group.users.count() == 1
    assert group.users.first() == user_1
