from django.urls import reverse


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
