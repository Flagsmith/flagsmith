import json

import pytest
from django.urls import reverse
from rest_framework import status
from tests.unit.environments.helpers import get_environment_user_client

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)


def test_user_without_update_feature_state_permission_cannot_create_identity_feature_state(
    client,
    organisation_one,
    organisation_one_project_one,
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_user,
    identity_one,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = get_environment_user_client(
        user=organisation_one_user,
        environment=environment,
        permission_keys=[VIEW_ENVIRONMENT],
    )

    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[environment.api_key, identity_one.id],
    )

    # When
    response = client.post(
        url,
        data=json.dumps({"feature": feature.id, "enabled": True}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "permission_keys, admin", (([], True), ([UPDATE_FEATURE_STATE], False))
)
def test_user_with_update_feature_state_permission_can_update_identity_feature_state(
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_project_one,
    organisation_one_user,
    organisation_one,
    identity_one,
    permission_keys,
    admin,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = get_environment_user_client(
        user=organisation_one_user,
        environment=environment,
        permission_keys=permission_keys,
        admin=admin,
    )

    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[environment.api_key, identity_one.id],
    )

    # When
    response = client.post(
        url,
        data=json.dumps({"feature": feature.id, "enabled": True}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
