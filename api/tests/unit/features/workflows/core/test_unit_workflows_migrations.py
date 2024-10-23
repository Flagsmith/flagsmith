import pytest
from django.conf import settings
from django_test_migrations.migrator import Migrator


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migrate_add_project_to_change_request(migrator: Migrator) -> None:
    old_state = migrator.apply_initial_migration(
        ("workflows_core", "0010_add_ignore_conflicts_option"),
    )
    OldOrganisation = old_state.apps.get_model("organisations", "Organisation")
    OldProject = old_state.apps.get_model("projects", "Project")
    OldEnvironment = old_state.apps.get_model("environments", "Environment")
    OldFFAdminUser = old_state.apps.get_model("users", "FFAdminUser")
    OldChangeRequest = old_state.apps.get_model("workflows_core", "ChangeRequest")

    organisation = OldOrganisation.objects.create(name="Test Org")
    project = OldProject.objects.create(name="Test Project", organisation=organisation)
    environment = OldEnvironment.objects.create(
        name="Test Environment", project=project
    )
    user = OldFFAdminUser.objects.create(email="staff@example.co")
    change_request = OldChangeRequest.objects.create(
        environment=environment, title="Test CR", user_id=user.id
    )

    assert hasattr(change_request, "project") is False

    # When
    new_state = migrator.apply_tested_migration(
        ("workflows_core", "0011_add_project_to_change_requests")
    )

    # Then
    NewChangeRequest = new_state.apps.get_model("workflows_core", "ChangeRequest")
    new_change_request = NewChangeRequest.objects.get(id=change_request.id)
    assert new_change_request.project_id == project.id
