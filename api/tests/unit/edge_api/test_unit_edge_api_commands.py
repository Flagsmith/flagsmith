from django.core.management import call_command
from pytest_mock import MockerFixture

from projects.models import EdgeV2MigrationStatus, Project


def test_migrate_to_edge_v2__new_projects__dont_migrate(
    mocker: MockerFixture, project: Project
) -> None:
    # Given
    # unmigrated projects are present
    unmigrated_projects = Project.objects.bulk_create(
        [
            Project(
                name="edge_v2_not_started",
                organisation=project.organisation,
                edge_v2_migration_status=EdgeV2MigrationStatus.NOT_STARTED,
                enable_dynamo_db=True,
            ),
            Project(
                name="edge_v2_incomplete",
                organisation=project.organisation,
                edge_v2_migration_status=EdgeV2MigrationStatus.INCOMPLETE,
                enable_dynamo_db=True,
            ),
        ],
    )

    migrate_project_environments_to_v2_mock = mocker.patch(
        "edge_api.management.commands.migrate_to_edge_v2.migrate_project_environments_to_v2",
        autospec=True,
    )

    # When
    call_command("migrate_to_edge_v2")

    # Then
    # unmigrated projects were migrated
    migrate_project_environments_to_v2_mock.assert_has_calls(
        [mocker.call(project.id) for project in unmigrated_projects]
    )
    # the migrated `project` was not redundantly migrated
    migrate_project_environments_to_v2_mock.call_count == len(unmigrated_projects)


def test_migrate_to_edge_v2__core_projects__dont_migrate(
    mocker: MockerFixture, project: Project
) -> None:
    # Given
    # unmigrated Core projects are present
    Project.objects.bulk_create(
        [
            Project(
                name="core__edge_v2_not_started",
                organisation=project.organisation,
                edge_v2_migration_status=EdgeV2MigrationStatus.NOT_STARTED,
                enable_dynamo_db=False,
            ),
            Project(
                name="core__edge_v2_incomplete",
                organisation=project.organisation,
                edge_v2_migration_status=EdgeV2MigrationStatus.INCOMPLETE,
                enable_dynamo_db=False,
            ),
        ],
    )

    migrate_project_environments_to_v2_mock = mocker.patch(
        "edge_api.management.commands.migrate_to_edge_v2.migrate_project_environments_to_v2",
        autospec=True,
    )

    # When
    call_command("migrate_to_edge_v2")

    # Then
    # unmigrated Core projects were not migrated
    migrate_project_environments_to_v2_mock.assert_not_called()
