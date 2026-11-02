import json

import pytest
from django.urls import reverse
from pytest_lazy_fixtures import lf as lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_update_feature_state_value__new_value_provided__updates_value(  # type: ignore[no-untyped-def]
    client, environment, environment_api_key, feature, feature_state
):
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state],
    )
    new_value = "new-value"
    data = {
        "id": feature_state,
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature,
        "environment": environment,
        "identity": None,
        "feature_segment": None,
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature_state_value"] == new_value


def test_update_feature_state__different_feature_segment__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature_state: int,
    feature_segment: int,
) -> None:
    # Given
    url = f"/api/v1/environments/{environment_api_key}/featurestates/{feature_state}/"

    # When
    response = admin_client.put(
        url,
        data={"feature_segment": feature_segment},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "feature_segment": ["Cannot change the feature segment of a feature state"]
    }
    assert admin_client.get(url).json()["feature_segment"] is None
