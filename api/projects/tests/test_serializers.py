from datetime import timedelta

from environments.dynamodb.migrator import IdentityMigrator
from projects.serializers import ProjectSerializer


def test_ProjectSerializer_get_use_edge_identities_calls_migrator_with_correct_arguments(
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    mocked_identity_migrator = mocker.patch(
        "projects.serializers.IdentityMigrator", spec=IdentityMigrator
    )
    mocked_identity_migrator.return_value.is_migration_done = True

    # When
    serializer = ProjectSerializer()

    # Then
    assert serializer.get_use_edge_identities(project) is True
    mocked_identity_migrator.assert_called_with(project.id)


def test_ProjectSerializer_get_use_edge_identities_returns_false_if_dynamo_table_name_is_not_set(
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None
    mocked_identity_migrator = mocker.patch("projects.serializers.IdentityMigrator")

    # When
    serializer = ProjectSerializer()

    # Then
    assert serializer.get_use_edge_identities(project) is False

    # and
    mocked_identity_migrator.assert_not_called()


def test_ProjectSerializer_get_use_edge_identities_true_when_edge_release_date_passed(
    mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    settings.EDGE_RELEASE_DATETIME = project.created_date - timedelta(days=1)

    mocked_identity_migrator = mocker.patch(
        "projects.serializers.IdentityMigrator", spec=IdentityMigrator
    )
    mocked_identity_migrator.return_value.is_migration_done = False

    serializer = ProjectSerializer()

    # When
    response = serializer.get_use_edge_identities(project)

    # Then
    assert response is True
