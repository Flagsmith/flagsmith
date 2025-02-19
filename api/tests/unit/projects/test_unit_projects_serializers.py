from datetime import timedelta

import pytest
from django.utils import timezone

from environments.dynamodb.types import ProjectIdentityMigrationStatus
from projects.serializers import (
    ProjectListSerializer,
    ProjectRetrieveSerializer,
)


def test_ProjectListSerializer_get_migration_status_returns_migration_not_applicable_if_not_configured(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None
    mocked_identity_migrator = mocker.patch(
        "projects.serializers.IdentityMigrator", autospec=True
    )

    serializer = ProjectListSerializer()

    # When
    migration_status = serializer.get_migration_status(project)

    # Then
    assert migration_status == ProjectIdentityMigrationStatus.NOT_APPLICABLE.value
    mocked_identity_migrator.assert_not_called()


def test_ProjectListSerializer_get_migration_status_returns_migration_completed_for_new_projects(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    settings.EDGE_RELEASE_DATETIME = project.created_date - timedelta(days=1)
    mocked_identity_migrator = mocker.patch(
        "projects.serializers.IdentityMigrator", autospec=True
    )

    serializer = ProjectListSerializer()

    # When
    migration_status = serializer.get_migration_status(project)

    # Then
    assert migration_status == ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value
    mocked_identity_migrator.assert_not_called()


def test_ProjectListSerializer_get_migration_status_calls_migrator_with_correct_arguments_for_old_projects(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    mocked_identity_migrator = mocker.patch(
        "projects.serializers.IdentityMigrator", autospec=True
    )

    settings.EDGE_RELEASE_DATETIME = timezone.now()

    serializer = ProjectListSerializer()

    # When
    migration_status = serializer.get_migration_status(project)

    # Then
    mocked_identity_migrator.assert_called_once_with(project.id)
    assert (
        migration_status == mocked_identity_migrator.return_value.migration_status.value
    )


@pytest.mark.parametrize(
    "migration_status, expected",
    [
        (ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value, True),
        (ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS.value, False),
        (ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED.value, False),
        (ProjectIdentityMigrationStatus.NOT_APPLICABLE.value, False),
    ],
)
def test_ProjectListSerializer_get_use_edge_identities(  # type: ignore[no-untyped-def]
    project, migration_status, expected
):
    # Given
    serializer = ProjectListSerializer(context={"migration_status": migration_status})

    # When/Then
    assert expected is serializer.get_use_edge_identities(project)


@pytest.mark.parametrize(
    "migration_status, expected",
    [
        (ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.value, True),
        (ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS.value, False),
        (ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED.value, False),
        (ProjectIdentityMigrationStatus.NOT_APPLICABLE.value, False),
    ],
)
def test_ProjectRetrieveSerializer_get_use_edge_identities(  # type: ignore[no-untyped-def]
    project, migration_status, expected
):
    # Given
    serializer = ProjectRetrieveSerializer(
        context={"migration_status": migration_status}
    )

    # When/Then
    assert expected is serializer.get_use_edge_identities(project)
