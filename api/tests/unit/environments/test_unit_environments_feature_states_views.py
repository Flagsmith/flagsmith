import json

import pytest
from django.urls import reverse
from rest_framework import status

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from tests.unit.environments.helpers import get_environment_user_client


def test_user_without_update_feature_state_permission_cannot_update_feature_state(
    client,
    organisation_one,
    organisation_one_project_one,
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_user,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = get_environment_user_client(
        user=organisation_one_user,
        environment=environment,
        permission_keys=[VIEW_ENVIRONMENT],
    )

    feature_state = environment.get_feature_state(feature_id=feature.id)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.patch(
        url,
        data=json.dumps({"feature_state_value": "something-else"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "permissions, admin",
    (([], True), ([VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE], False)),
)
def test_permitted_user_can_update_feature_state(
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_project_one,
    organisation_one_user,
    organisation_one,
    permissions,
    admin,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = get_environment_user_client(
        user=organisation_one_user,
        environment=environment,
        permission_keys=permissions,
        admin=admin,
    )

    feature_state = environment.get_feature_state(feature_id=feature.id)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.patch(
        url, data=json.dumps({"enabled": True}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_user_with_view_environment_can_retrieve_feature_state(
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_user,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    feature_state = environment.get_feature_state(feature_id=feature.id)
    client = get_environment_user_client(
        user=organisation_one_user,
        environment=environment,
        permission_keys=[VIEW_ENVIRONMENT],
        admin=False,
    )

    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == feature_state.id
