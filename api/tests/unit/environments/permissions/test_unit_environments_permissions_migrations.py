import pytest
from django.conf import settings

from environments.permissions.constants import (
    APPROVE_CHANGE_REQUEST,
    CREATE_CHANGE_REQUEST,
    MANAGE_IDENTITIES,
    UPDATE_FEATURE_STATE,
    VIEW_IDENTITIES,
)

if settings.SKIP_MIGRATION_TESTS is True:
    pytest.skip(
        "Skip migration tests to speed up tests where necessary",
        allow_module_level=True,
    )


def test_add_change_request_permissions_adds_correct_permissions_if_user_has_update_fs(
    django_user_model, migrator
):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environment_permissions", "0003_add_manage_identities_permission")
    )
    user_model = old_state.apps.get_model("users", "FFAdminUser")
    user_environment_permission_model = old_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    permission_model = old_state.apps.get_model("permissions", "PermissionModel")
    organisation_model = old_state.apps.get_model("organisations", "Organisation")
    project_model = old_state.apps.get_model("projects", "Project")
    environment_model = old_state.apps.get_model("environments", "Environment")

    org = organisation_model.objects.create(name="test org")
    project = project_model.objects.create(name="test project", organisation=org)
    environment = environment_model.objects.create(name="test env", project=project)

    # a user with UPDATE_FEATURE_STATE permission
    user = user_model.objects.create(email="test@example.com")
    user_environment_permission = user_environment_permission_model.objects.create(
        user=user, environment=environment
    )
    update_feature_state_permission = permission_model.objects.get(
        key=UPDATE_FEATURE_STATE
    )
    user_environment_permission.permissions.add(update_feature_state_permission)

    # When
    new_state = migrator.apply_tested_migration(
        ("environment_permissions", "0004_add_change_request_permissions")
    )
    # Then
    new_user_environment_permission_model = new_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )

    new_user_environment_permission = new_user_environment_permission_model.objects.get(
        id=user_environment_permission.id
    )
    assert new_user_environment_permission.permissions.count() == 3
    assert list(
        new_user_environment_permission.permissions.order_by("key").values_list(
            flat=True
        )
    ) == [APPROVE_CHANGE_REQUEST, CREATE_CHANGE_REQUEST, UPDATE_FEATURE_STATE]


def test_add_change_request_permissions_does_nothing_if_user_does_not_have_update_fs(
    environment, django_user_model, migrator
):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environment_permissions", "0003_add_manage_identities_permission")
    )
    user_model = old_state.apps.get_model("users", "FFAdminUser")
    organisation_model = old_state.apps.get_model("organisations", "Organisation")
    project_model = old_state.apps.get_model("projects", "Project")
    environment_model = old_state.apps.get_model("environments", "Environment")

    org = organisation_model.objects.create(name="test org")
    project = project_model.objects.create(name="test project", organisation=org)
    environment = environment_model.objects.create(name="test env", project=project)

    # a user without UPDATE_FEATURE_STATE permission
    user = user_model.objects.create(email="test@example.com")

    # When
    new_state = migrator.apply_tested_migration(
        ("environment_permissions", "0004_add_change_request_permissions")
    )

    # Then
    assert (
        not new_state.apps.get_model(
            "environment_permissions", "UserEnvironmentPermission"
        )
        .objects.filter(user_id=user.id, environment_id=environment.id)
        .exists()
    )


def test_add_view_identity_permissions_adds_view_permissions_if_user_has_manage_identities(
    environment, django_user_model, migrator
):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environment_permissions", "0004_add_change_request_permissions")
    )
    user_model = old_state.apps.get_model("users", "FFAdminUser")
    user_group_model = old_state.apps.get_model("users", "UserPermissionGroup")
    user_environment_permission_model = old_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    user_permission_group_environment_permission = old_state.apps.get_model(
        "environment_permissions", "UserPermissionGroupEnvironmentPermission"
    )
    permission_model = old_state.apps.get_model("permissions", "PermissionModel")
    organisation_model = old_state.apps.get_model("organisations", "Organisation")
    project_model = old_state.apps.get_model("projects", "Project")
    environment_model = old_state.apps.get_model("environments", "Environment")

    org = organisation_model.objects.create(name="test org")
    project = project_model.objects.create(name="test project", organisation=org)
    environment = environment_model.objects.create(name="test env", project=project)

    manage_identities_permission = permission_model.objects.get(key=MANAGE_IDENTITIES)

    # a user with MANAGE_IDENTITIES permission
    user = user_model.objects.create(email="test@example.com")
    user_environment_permission = user_environment_permission_model.objects.create(
        user=user, environment=environment
    )
    user_environment_permission.permissions.add(manage_identities_permission)

    # and a group with MANAGE_IDENTITIES permission
    user_group = user_group_model.objects.create(name="test", organisation=org)
    user_environment_permission_group = (
        user_permission_group_environment_permission.objects.create(
            environment=environment, group=user_group
        )
    )
    user_environment_permission_group.permissions.add(manage_identities_permission)

    # When
    new_state = migrator.apply_tested_migration(
        ("environment_permissions", "0005_add_view_identity_permissions")
    )

    # Then
    new_user_environment_permission_model = new_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    new_user_permission_group_environment_permission_model = new_state.apps.get_model(
        "environment_permissions", "UserPermissionGroupEnvironmentPermission"
    )
    new_user_environment_permission = new_user_environment_permission_model.objects.get(
        id=user_environment_permission.id
    )
    new_user_group_permission = (
        new_user_permission_group_environment_permission_model.objects.get(
            id=user_environment_permission_group.id
        )
    )
    assert new_user_environment_permission.permissions.count() == 2
    assert new_user_group_permission.permissions.count() == 2
    assert list(
        new_user_environment_permission.permissions.order_by("key").values_list(
            flat=True
        )
    ) == [
        MANAGE_IDENTITIES,
        VIEW_IDENTITIES,
    ]

    assert list(
        new_user_group_permission.permissions.order_by("key").values_list(flat=True)
    ) == [
        MANAGE_IDENTITIES,
        VIEW_IDENTITIES,
    ]


def test_add_view_identity_permissions_does_nothing_if_user_does_not_have_manage_identities(
    environment, django_user_model, migrator
):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environment_permissions", "0004_add_change_request_permissions")
    )
    user_model = old_state.apps.get_model("users", "FFAdminUser")
    user_environment_permission_model = old_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    permission_model = old_state.apps.get_model("permissions", "PermissionModel")
    organisation_model = old_state.apps.get_model("organisations", "Organisation")
    project_model = old_state.apps.get_model("projects", "Project")
    environment_model = old_state.apps.get_model("environments", "Environment")

    org = organisation_model.objects.create(name="test org")
    project = project_model.objects.create(name="test project", organisation=org)
    environment = environment_model.objects.create(name="test env", project=project)

    # a user with UPDATE_FEATURE_STATE permission
    user = user_model.objects.create(email="test@example.com")
    user_environment_permission = user_environment_permission_model.objects.create(
        user=user, environment=environment
    )
    update_feature_state_permission = permission_model.objects.get(
        key=UPDATE_FEATURE_STATE
    )
    user_environment_permission.permissions.add(update_feature_state_permission)

    # When
    new_state = migrator.apply_tested_migration(
        ("environment_permissions", "0005_add_view_identity_permissions")
    )

    # Then
    new_user_environment_permission_model = new_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )

    new_user_environment_permission = new_user_environment_permission_model.objects.get(
        id=user_environment_permission.id
    )
    assert new_user_environment_permission.permissions.count() == 1
    assert (
        new_user_environment_permission.permissions.first().key == UPDATE_FEATURE_STATE
    )


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_merge_duplicate_permissions_migration(migrator):
    # Given - the migration state is at 0016 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("environment_permissions", "0005_add_view_identity_permissions")
    )
    # Next, fetch model classes we are going to use
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Environment = old_state.apps.get_model("environments", "Environment")

    UserModel = old_state.apps.get_model("users", "FFAdminUser")
    UserPermissionGroup = old_state.apps.get_model("users", "UserPermissionGroup")

    UserEnvironmentPermission = old_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    UserPermissionGroupEnvironmentPermission = old_state.apps.get_model(
        "environment_permissions", "UserPermissionGroupEnvironmentPermission"
    )

    # Next, create some setup data
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment = Environment.objects.create(name="Test environment", project=project)
    test_user = UserModel.objects.create(email="test_user@mail.com")
    admin_user = UserModel.objects.create(email="admin_user@mail.com")
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test User Permission Group", organisation=organisation
    )
    non_duplicate_permission = UserEnvironmentPermission.objects.create(
        user=admin_user, environment=environment
    )
    # Now - Let's create duplicate permissions
    first_permission = UserEnvironmentPermission.objects.create(
        user=test_user, environment=environment
    )
    first_permission.permissions.add(UPDATE_FEATURE_STATE)

    second_permission = UserEnvironmentPermission.objects.create(
        user=test_user, environment=environment
    )
    second_permission.permissions.add(UPDATE_FEATURE_STATE)
    second_permission.permissions.add(APPROVE_CHANGE_REQUEST)

    UserEnvironmentPermission.objects.create(
        user=test_user, environment=environment, admin=True
    )

    # Next, let's create duplicate permissions using a group
    first_group_permission = UserPermissionGroupEnvironmentPermission.objects.create(
        group_id=user_permission_group.id, environment_id=environment.id
    )
    first_group_permission.permissions.add(UPDATE_FEATURE_STATE)

    second_group_permission = UserPermissionGroupEnvironmentPermission.objects.create(
        group=user_permission_group, environment=environment
    )
    second_group_permission.permissions.add(UPDATE_FEATURE_STATE)
    second_group_permission.permissions.add(APPROVE_CHANGE_REQUEST)

    UserPermissionGroupEnvironmentPermission.objects.create(
        group=user_permission_group, environment=environment, admin=True
    )

    # When - we run the migration
    new_state = migrator.apply_tested_migration(
        ("environment_permissions", "0006_merge_duplicate_permissions")
    )
    NewUserEnvironmentPermission = new_state.apps.get_model(
        "environment_permissions", "UserEnvironmentPermission"
    )
    NewUserPermissionGroupEnvironmentPermission = new_state.apps.get_model(
        "environment_permissions", "UserPermissionGroupEnvironmentPermission"
    )
    # Then - we expect the duplicate permissions to be merged
    merged_permission = NewUserEnvironmentPermission.objects.get(
        user_id=test_user.id, environment_id=environment.id
    )
    assert {APPROVE_CHANGE_REQUEST, UPDATE_FEATURE_STATE} == set(
        merged_permission.permissions.values_list("key", flat=True)
    )
    assert merged_permission.admin is True

    merged_group_permission = NewUserPermissionGroupEnvironmentPermission.objects.get(
        group=user_permission_group.id, environment=environment.id
    )
    assert {APPROVE_CHANGE_REQUEST, UPDATE_FEATURE_STATE} == set(
        merged_permission.permissions.values_list("key", flat=True)
    )
    assert merged_group_permission.admin is True

    # and non_duplicate permission still exists
    assert UserEnvironmentPermission.objects.filter(
        id=non_duplicate_permission.id
    ).exists()
