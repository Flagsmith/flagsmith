from django.urls import reverse
from rest_framework import status


def test_create_role(organisation, admin_client):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    data = {"name": "a role", "organisation": organisation.id}

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
