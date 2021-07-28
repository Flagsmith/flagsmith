from django.urls import reverse
from rest_framework import status


def test_clone_environment_returns_200(
    admin_client, project, environment, environment_api_key
):
    # Given
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])
    # When
    res = admin_client.post(url, {"name": env_name})

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == env_name
