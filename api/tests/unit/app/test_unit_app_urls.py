from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_health_check_endpoint_returns_200(db: None, api_client: APIClient):
    # Given
    base_url = reverse("health:health_check_home")
    url = base_url + "?format=json"

    # When
    res = api_client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK
