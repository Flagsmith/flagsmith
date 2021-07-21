from django.urls import reverse
from rest_framework import status


def test_clone_environment_returns_200(admin_client, environment_dict):
    url = reverse(
        "api-v1:environments:environment-clone", args=[environment_dict["api_key"]]
    )

    res = admin_client.post(url, {"name": "clone-env"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == "clone-env"
