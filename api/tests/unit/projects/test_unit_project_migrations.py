import pytest
from common.projects.permissions import CREATE_ENVIRONMENT, VIEW_PROJECT
from django.conf import settings


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_merge_duplicate_permissions_migration(migrator):
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
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_make_project_name_unique_per_organisation_migration(migrator):
    # Given - the migration state is at 0026 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("projects", "0026_add_change_request_approval_limit_to_projects")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")

    organisation = Organisation.objects.create(name="Test Organisation")

    duplicate_project_name = "Duplicate project"
    project_1 = Project.objects.create(name=duplicate_project_name, organisation=organisation)
    duplicate_project = Project.objects.create(name=duplicate_project_name, organisation=organisation)

    non_duplicate_project_name = "Non duplicate project"
    non_duplicate_project = Project.objects.create(name=non_duplicate_project_name, organisation=organisation)

    # When - we run the migration
    new_state = migrator.apply_tested_migration(
        ("projects", "0027_make_project_name_unique_per_organisation")
    )
    NewProject = new_state.apps.get_model("projects", "Project")

    # Then
    assert NewProject.objects.get(id=project_1.id).name == duplicate_project_name
    assert NewProject.objects.get(id=duplicate_project.id).name == f"{duplicate_project_name} (1)"
    assert NewProject.objects.get(id=non_duplicate_project.id).name == non_duplicate_project_name
