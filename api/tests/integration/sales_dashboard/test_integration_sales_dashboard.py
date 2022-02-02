from django.urls import reverse
from rest_framework import status


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


def test_migrate_identities_to_edge_calls_migrate_identity_with_correct_arguments(
    superuser_authenticated_client, mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch("sales_dashboard.views.DynamoIdentityWrapper")
    url = reverse("sales_dashboard:migrate_identities", args=[project])

    # When
    response = superuser_authenticated_client.post(url)

    # Then
    assert response.status_code == status.HTTP_302_FOUND
    mocked_dynamo_wrapper.assert_called_with()
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_called_with(project)
