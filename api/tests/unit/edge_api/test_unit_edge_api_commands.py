import typing

from django.core.management import call_command
from pytest_mock import MockerFixture

from edge_api.management.commands.ensure_identity_traits_blanks import (
    identity_wrapper,
)
from projects.models import EdgeV2MigrationStatus, Project

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


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


def test_ensure_identity_traits_blanks__calls_expected(
    flagsmith_identities_table: "Table",
    mocker: MockerFixture,
) -> None:
    # Given
    environment_api_key = "test"
    identity_without_traits = {
        "composite_key": f"{environment_api_key}_identity_without_traits",
        "environment_api_key": environment_api_key,
        "identifier": "identity_without_traits",
        "identity_uuid": "8208c268-e286-4bff-848a-e4b97032fca9",
    }
    identity_with_correct_traits = {
        "composite_key": f"{environment_api_key}_identity_with_correct_traits",
        "identifier": "identity_with_correct_traits",
        "environment_api_key": environment_api_key,
        "identity_uuid": "1a47c1e2-4a9d-4f45-840e-a4cf1a23329e",
        "identity_traits": [{"trait_key": "key", "trait_value": "value"}],
    }
    identity_with_skipped_blank_trait_value = {
        "composite_key": f"{environment_api_key}_identity_with_skipped_blank_trait_value",
        "identifier": "identity_with_skipped_blank_trait_value",
        "environment_api_key": environment_api_key,
        "identity_uuid": "33e11400-3a34-4b09-9541-3c99e9bf713a",
        "identity_traits": [
            {"trait_key": "key", "trait_value": "value"},
            {"trait_key": "blank"},
        ],
    }
    fixed_identity_with_skipped_blank_trait_value = {
        **identity_with_skipped_blank_trait_value,
        "identity_traits": [
            {"trait_key": "key", "trait_value": "value"},
            {"trait_key": "blank", "trait_value": ""},
        ],
    }

    flagsmith_identities_table.put_item(Item=identity_without_traits)
    flagsmith_identities_table.put_item(Item=identity_with_correct_traits)
    flagsmith_identities_table.put_item(Item=identity_with_skipped_blank_trait_value)

    identity_wrapper_put_item_mock = mocker.patch(
        "edge_api.management.commands.ensure_identity_traits_blanks.identity_wrapper.put_item",
        side_effect=identity_wrapper.put_item,
    )

    # When
    call_command("ensure_identity_traits_blanks")

    # Then
    assert flagsmith_identities_table.scan()["Items"] == [
        identity_without_traits,
        identity_with_correct_traits,
        fixed_identity_with_skipped_blank_trait_value,
    ]
    identity_wrapper_put_item_mock.assert_called_once_with(
        fixed_identity_with_skipped_blank_trait_value,
    )
