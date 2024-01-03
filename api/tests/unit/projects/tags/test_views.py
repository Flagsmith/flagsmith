import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project
from projects.tags.models import Tag


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_get_tag_by_uuid(client: APIClient, project: Project, tag: Tag):
    url = reverse("api-v1:projects:tags-get-by-uuid", args=[project.id, str(tag.uuid)])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(tag.uuid)
