from django.urls import reverse
from rest_framework import status


def test_returns_404_when_user_exists(admin_user, django_client):
    # Given
    url = reverse("api-v1:users:config-init")

    # When
    get_response = django_client.get(url)
    post_response = django_client.post(url)

    # Then
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
    assert post_response.status_code == status.HTTP_404_NOT_FOUND


def test_returns_200_when_no_user_exists(db, django_client):
    # Given
    url = reverse("api-v1:users:config-init")

    # When
    response = django_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
