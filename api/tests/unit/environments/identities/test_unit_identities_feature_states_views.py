import json

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from features.models import Feature, FeatureState, FeatureStateValue
from projects.models import Project
from tests.unit.environments.helpers import get_environment_user_client


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


def test_user_with_view_environment_permission_can_retrieve_all_feature_states_for_identity(
    environment,
    identity,
    test_user_client,
    view_environment_permission,
    user_environment_permission,
):
    # Given
    user_environment_permission.permissions.add(view_environment_permission)

    url = reverse(
        "api-v1:environments:identity-featurestates-all",
        args=(environment.api_key, identity.id),
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_identity_clone_flag_states_from(
    project: Project,
    environment: Environment,
    admin_client: Client,
) -> None:

    def features_for_identity_clone_flag_states_from(
        project: Project,
    ) -> tuple[Feature, ...]:
        features: list[Feature] = []
        for i in range(1, 4):
            features.append(
                Feature.objects.create(
                    name=f"feature_{i}", project=project, default_enabled=True
                )
            )
        return tuple(features)

    # Given
    feature_1, feature_2, feature_3 = features_for_identity_clone_flag_states_from(
        project
    )

    source_identity: Identity = Identity.objects.create(
        identifier="source_identity", environment=environment
    )
    target_identity: Identity = Identity.objects.create(
        identifier="target_identity", environment=environment
    )

    source_feature_state_1: FeatureState = FeatureState.objects.create(
        feature=feature_1,
        environment=environment,
        identity=source_identity,
        enabled=True,
    )
    source_feature_state_1_value = "Source Identity for feature value 1"
    FeatureStateValue.objects.filter(feature_state=source_feature_state_1).update(
        string_value=source_feature_state_1_value
    )

    source_feature_state_2: FeatureState = FeatureState.objects.create(
        feature=feature_2,
        environment=environment,
        identity=source_identity,
        enabled=True,
    )
    source_feature_state_2_value = "Source Identity for feature value 2"
    FeatureStateValue.objects.filter(feature_state=source_feature_state_2).update(
        string_value=source_feature_state_2_value
    )

    target_feature_state_2: FeatureState = FeatureState.objects.create(
        feature=feature_2,
        environment=environment,
        identity=target_identity,
        enabled=False,
    )
    target_feature_state_2_value = "Target Identity value for feature 2"
    FeatureStateValue.objects.filter(feature_state=target_feature_state_2).update(
        string_value=target_feature_state_2_value
    )

    FeatureState.objects.create(
        feature=feature_3,
        environment=environment,
        identity=target_identity,
        enabled=False,
    )

    clone_identity_feature_states_url = reverse(
        "api-v1:environments:identity-featurestates-clone-from-given-identity",
        args=[environment.api_key, target_identity.id],
    )

    # When
    clone_identity_feature_states_response = admin_client.post(
        clone_identity_feature_states_url,
        data=json.dumps({"source_identity_id": str(source_identity.id)}),
        content_type="application/json",
    )

    # Then
    assert clone_identity_feature_states_response.status_code == status.HTTP_200_OK

    response = clone_identity_feature_states_response.json()

    # Target identity contains only the 2 cloned overridden features states and 1 environment feature state
    assert len(response) == 3

    # Assert cloned data is correct
    assert response[0]["feature"]["id"] == feature_1.id
    assert response[0]["enabled"] == source_feature_state_1.enabled
    assert response[0]["feature_state_value"] == source_feature_state_1_value
    assert response[0]["overridden_by"] == "IDENTITY"

    assert response[1]["feature"]["id"] == feature_2.id
    assert response[1]["enabled"] == source_feature_state_2.enabled
    assert response[1]["feature_state_value"] == source_feature_state_2_value
    assert response[1]["overridden_by"] == "IDENTITY"

    assert response[2]["feature"]["id"] == feature_3.id
    assert response[2]["enabled"] == feature_3.default_enabled
    assert response[2]["feature_state_value"] == feature_3.initial_value
    assert response[2]["overridden_by"] is None

    # Target identity feature 3 override has been removed
    assert not FeatureState.objects.filter(
        feature=feature_3,
        environment=environment,
        identity=target_identity,
    ).exists()
