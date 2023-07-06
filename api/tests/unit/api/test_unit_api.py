import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.parametrize(
    "client", (lazy_fixture("api_client"), lazy_fixture("admin_client"))
)
def test_swagger_docs_generation(client: APIClient) -> None:
    url = reverse("api-v1:schema-swagger-ui")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
