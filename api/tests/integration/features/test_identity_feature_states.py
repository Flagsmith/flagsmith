import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature
from projects.models import Project


@pytest.mark.django_db
def test_list_features__with_identity__returns_identity_feature_state(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
    identity: Identity,
) -> None:
    # Given - create an identity override
    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[environment.api_key, identity.id],
    )
    data = {
        "feature": feature.id,
        "enabled": True,
        "feature_state_value": {"type": "unicode", "string_value": "identity-override"},
    }
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    # When
    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = f"{features_url}?environment={environment.id}&identity={identity.id}"
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert feature_data["id"] == feature.id
    assert feature_data["identity_feature_state"] is not None
    assert feature_data["identity_feature_state"]["enabled"] is True
    assert (
        feature_data["identity_feature_state"]["feature_state_value"]
        == "identity-override"
    )


@pytest.mark.django_db
def test_list_features__without_identity_param__identity_feature_state_is_none(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = f"{features_url}?environment={environment.id}"

    # When
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert "identity_feature_state" in feature_data
    assert feature_data["identity_feature_state"] is None


@pytest.mark.django_db
def test_list_features__with_invalid_identity_id__identity_feature_state_is_none(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = f"{features_url}?environment={environment.id}&identity=999999"

    # When
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert feature_data["identity_feature_state"] is None


@pytest.mark.django_db
def test_list_features__with_edge_project__identity_feature_state_is_none(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = f"{features_url}?environment={environment.id}&identity=59efa2a7-6a45-46d6-b953-a7073a90eacf"

    # When
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert feature_data["identity_feature_state"] is None


@pytest.mark.django_db
def test_list_features__with_identity_from_different_environment__identity_feature_state_is_none(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
    identity: Identity,
) -> None:
    # Given
    other_environment = Environment.objects.create(
        name="other-environment",
        project=project,
    )

    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = (
        f"{features_url}?environment={other_environment.id}&identity={identity.id}"
    )

    # When
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert feature_data["identity_feature_state"] is None


@pytest.mark.django_db
def test_list_features__with_identity_no_override__identity_feature_state_is_none(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
    identity: Identity,
) -> None:
    # Given - identity exists but has no override
    features_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    list_url = f"{features_url}?environment={environment.id}&identity={identity.id}"

    # When
    list_response = admin_client_new.get(list_url)

    # Then
    assert list_response.status_code == status.HTTP_200_OK
    feature_data = list_response.json()["results"][0]
    assert feature_data["identity_feature_state"] is None
