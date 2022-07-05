from django.urls import reverse
from rest_framework import status

from environments.dynamodb.migrator import IdentityMigrator


def test_sales_dashboard_index(superuser_authenticated_client):
    """
    VERY basic test to check that the index page loads.
    """

    # Given
    url = reverse("sales_dashboard:index")

    # When
    response = superuser_authenticated_client.get(url)

    # Then
    assert response.status_code == 200


def test_migrate_identities_to_edge_calls_identity_migrator_with_correct_arguments_if_migration_is_not_done(
    superuser_authenticated_client, mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    mocked_identity_migrator = mocker.patch(
        "sales_dashboard.views.IdentityMigrator", spec=IdentityMigrator
    )

    mocked_identity_migrator.return_value.can_migrate = True

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_302_FOUND
    mocked_identity_migrator.assert_called_with(project)
    mocked_identity_migrator.return_value.start_migration.assert_called_once_with()


def test_migrate_identities_to_edge_does_not_call_migrate_if_migration_is_already_done(
    superuser_authenticated_client, mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    mocked_identity_migrator = mocker.patch(
        "sales_dashboard.views.IdentityMigrator", spec=IdentityMigrator
    )

    mocked_identity_migrator.return_value.can_migrate = False

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mocked_identity_migrator.assert_called_with(project)
    mocked_identity_migrator.return_value.start_migration.assert_not_called()


def test_migrate_identities_to_edge_returns_400_if_dynamodb_is_not_enabled(
    superuser_authenticated_client, mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_migrate_identities_to_edge_calls_send_migration_event_with_correct_arguments(
    superuser_authenticated_client, mocker, project, settings, identity
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = "project_metadata_table"
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    mocked_identity_migrator = mocker.patch(
        "sales_dashboard.views.IdentityMigrator", spec=IdentityMigrator
    )

    mocked_identity_migrator.return_value.can_migrate = True

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_302_FOUND

    mocked_identity_migrator.assert_called_with(project)
    mocked_identity_migrator.return_value.start_migration.assert_called_once_with()
