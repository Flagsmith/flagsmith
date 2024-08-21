from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


def test_get_current_user(staff_user: FFAdminUser, staff_client: APIClient) -> None:
    # Given
    url = reverse("api-v1:custom_auth:ffadminuser-me")

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["email"] == staff_user.email
    assert response_json["first_name"] == staff_user.first_name
    assert response_json["last_name"] == staff_user.last_name
    assert response_json["uuid"] == str(staff_user.uuid)
