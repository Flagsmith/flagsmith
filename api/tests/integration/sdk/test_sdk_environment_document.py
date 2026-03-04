from rest_framework import status
from rest_framework.test import APIClient

from features.versioning.tasks import enable_v2_versioning


def test_get_environment_document__v2_versioning_with_identity_override__identity_features_populated(
    server_side_sdk_client: APIClient,
    feature: int,
    identity_featurestate: int,
    environment: int,
) -> None:
    """Reproduce https://github.com/Flagsmith/flagsmith/issues/6839

    When Feature Versioning v2 is enabled, identity overrides should still
    appear in the SDK document with their identity_features populated.
    """

    # Given - v2 feature versioning is enabled after identity override exists
    enable_v2_versioning(environment)

    # When
    url = "/api/v1/environment-document/"
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    identity_overrides = response.json()["identity_overrides"]
    assert len(identity_overrides) == 1

    identity_override = identity_overrides[0]
    assert len(identity_override["identity_features"]) > 0
    assert identity_override["identity_features"][0]["feature"]["id"] == feature
