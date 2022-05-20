import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status


@pytest.mark.parametrize(
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
)
def test_create_feature_state_for_identity_override(
    client, environment, identity, feature
):
    # Given
    create_url = reverse("api-v1:features:featurestates-list")
    data = {
        "enabled": True,
        "feature_state_value": {"type": "unicode", "string_value": "test value"},
        "identity": identity,
        "environment": environment,
        "feature": feature,
    }

    # When
    response = client.post(
        create_url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
)
def test_list_feature_states_for_environment(client, environment, feature):
    # Given
    base_url = reverse("api-v1:features:featurestates-list")
    url = f"{base_url}?environment={environment}"

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["environment"] == environment
