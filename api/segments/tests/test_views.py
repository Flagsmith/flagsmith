import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_with_required_metadata_returns_201(
    project,
    client,
    required_a_segment_metadata_field,
    optional_b_environment_metadata_field,
):
    # Given
    url = reverse("api-v1:environments:environment-list")
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test environment",
        "project": project.id,
        "description": description,
        "metadata": [
            {
                "model_field": required_a_segment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_segment_metadata_field.field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)
