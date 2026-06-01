import pytest
from common.projects.permissions import (
    CREATE_ENVIRONMENT,
    VIEW_PROJECT,
)
from django.conf import settings as test_settings
from django_test_migrations.migrator import Migrator


def test_merge_duplicate_permissions__duplicates_exist__merges_correctly(
    migrator: Migrator,
) -> None:
    # Given - the migration state is at 0016 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("projects", "0016_soft_delete_projects")
    )
    # Next, fetch model classes we are going to use
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")

    UserModel = old_state.apps.get_model("users", "FFAdminUser")
    UserPermissionGroup = old_state.apps.get_model("users", "UserPermissionGroup")

    UserProjectPermission = old_state.apps.get_model(
        "projects", "UserProjectPermission"
    )
    UserPermissionGroupProjectPermission = old_state.apps.get_model(
        "projects", "UserPermissionGroupProjectPermission"
    )

    # Next, create some setup data
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    test_user = UserModel.objects.create(email="test_user@mail.com")
    admin_user = UserModel.objects.create(email="admin_user@mail.com")
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test User Permission Group", organisation=organisation
    )
    non_duplicate_permission = UserProjectPermission.objects.create(
        user_id=admin_user.id, project_id=project.id
    )
    # Now - Let's create duplicate permissions
    first_permission = UserProjectPermission.objects.create(
        user_id=test_user.id, project_id=project.id
    )
    first_permission.permissions.add(VIEW_PROJECT)

    second_permission = UserProjectPermission.objects.create(
        user_id=test_user.id, project_id=project.id
    )
    second_permission.permissions.add(VIEW_PROJECT)
    second_permission.permissions.add(CREATE_ENVIRONMENT)

    UserProjectPermission.objects.create(user=test_user, project=project, admin=True)

    # Next, let's create duplicate permissions using a group
    first_group_permission = UserPermissionGroupProjectPermission.objects.create(
        group_id=user_permission_group.id, project_id=project.id
    )
    first_group_permission.permissions.add(VIEW_PROJECT)

    second_group_permission = UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project
    )
    second_group_permission.permissions.add(VIEW_PROJECT)
    second_group_permission.permissions.add(CREATE_ENVIRONMENT)

    UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project, admin=True
    )

    # When - we run the migration
    new_state = migrator.apply_tested_migration(
        ("projects", "0017_merge_duplicate_permissions")
    )
    NewUserProjectPermission = new_state.apps.get_model(
        "projects", "UserProjectPermission"
    )
    NewUserPermissionGroupProjectPermission = new_state.apps.get_model(
        "projects", "UserPermissionGroupProjectPermission"
    )
    # Then - we expect the duplicate permissions to be merged
    merged_permission = NewUserProjectPermission.objects.get(
        user_id=test_user.id, project_id=project.id
    )
    assert {CREATE_ENVIRONMENT, VIEW_PROJECT} == set(
        merged_permission.permissions.values_list("key", flat=True)
    )
    assert merged_permission.admin is True

    merged_group_permission = NewUserPermissionGroupProjectPermission.objects.get(
        group=user_permission_group.id, project=project.id
    )
    assert {CREATE_ENVIRONMENT, VIEW_PROJECT} == set(
        merged_permission.permissions.values_list("key", flat=True)
    )
    assert merged_group_permission.admin is True

    # and non_duplicate permission still exists
    assert UserProjectPermission.objects.filter(id=non_duplicate_permission.id).exists()


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_bump_default_project_limits__values_below_new_defaults__raised_to_new_defaults(
    migrator: Migrator,
) -> None:
    # Given - the migration state is at 0028 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("projects", "0028_add_enforce_feature_owners_to_project")
    )
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")

    organisation = Organisation.objects.create(name="Test Organisation")

    # A project whose limits were explicitly lowered below the new defaults.
    low_project = Project.objects.create(
        name="Low limits project",
        organisation=organisation,
        max_features_allowed=50,
        max_segments_allowed=10,
        max_segment_overrides_allowed=5,
    )
    # A project that still has the previous defaults (400 / 100 / 100).
    default_project = Project.objects.create(
        name="Default limits project",
        organisation=organisation,
    )
    # A project whose limits were explicitly raised above the new defaults.
    high_project = Project.objects.create(
        name="High limits project",
        organisation=organisation,
        max_features_allowed=5000,
        max_segments_allowed=5000,
        max_segment_overrides_allowed=5000,
    )

    # When - we run the migration
    new_state = migrator.apply_tested_migration(
        ("projects", "0029_bump_default_project_limits")
    )
    NewProject = new_state.apps.get_model("projects", "Project")

    # Then - projects below the new defaults are bumped up to them
    low_project_after = NewProject.objects.get(id=low_project.id)
    assert low_project_after.max_features_allowed == 1000
    assert low_project_after.max_segments_allowed == 500
    assert low_project_after.max_segment_overrides_allowed == 2000

    default_project_after = NewProject.objects.get(id=default_project.id)
    assert default_project_after.max_features_allowed == 1000
    assert default_project_after.max_segments_allowed == 500
    assert default_project_after.max_segment_overrides_allowed == 2000

    # And - projects already above the new defaults are left alone
    high_project_after = NewProject.objects.get(id=high_project.id)
    assert high_project_after.max_features_allowed == 5000
    assert high_project_after.max_segments_allowed == 5000
    assert high_project_after.max_segment_overrides_allowed == 5000
