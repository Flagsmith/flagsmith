from django.urls import reverse
from rest_framework import status

from environments.dynamodb.migrator import IdentityMigrator
from organisations.models import Organisation


def test_sales_dashboard_index__multiple_organisations__returns_200(  # type: ignore[no-untyped-def]
    superuser_authenticated_client, django_assert_num_queries
):
    """
    VERY basic test to check that the index page loads.
    """

    # Given
    url = reverse("sales_dashboard:index")

    # create some organisations so we can ensure there aren't any N+1 issues
    for i in range(10):
        Organisation.objects.create(name=f"Test organisation {i}")

    # When
    with django_assert_num_queries(5):
        response = superuser_authenticated_client.get(url)

    # Then
    assert response.status_code == 200


def test_migrate_identities_to_edge__migration_not_done__triggers_migration(  # type: ignore[no-untyped-def]
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
    mocked_identity_migrator.return_value.trigger_migration.assert_called_once_with()


def test_migrate_identities_to_edge__migration_already_done__returns_400(  # type: ignore[no-untyped-def]
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
    mocked_identity_migrator.return_value.trigger_migration.assert_not_called()


def test_migrate_identities_to_edge__dynamodb_not_enabled__returns_400(  # type: ignore[no-untyped-def]
    superuser_authenticated_client, mocker, project, settings
):
    # Given
    settings.PROJECT_METADATA_TABLE_NAME_DYNAMO = None
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_migrate_identities_to_edge__can_migrate__triggers_migration(  # type: ignore[no-untyped-def]
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
    mocked_identity_migrator.return_value.trigger_migration.assert_called_once_with()
