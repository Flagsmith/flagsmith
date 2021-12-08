from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_user_without_update_feature_state_permission_cannot_update_feature_state(
    client,
    organisation_one,
    organisation_one_project_one,
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    environment_one_viewer_user,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = APIClient()
    client.force_authenticate(environment_one_viewer_user)

    feature_state = environment.get_feature_state(feature_id=feature.id)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.patch(url, data={"feature_state_value": "something-else"})

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_with_update_feature_state_permission_can_update_feature_state(
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    organisation_one_project_one,
    environment_one_feature_state_updater_user,
    organisation_one,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = APIClient()
    client.force_authenticate(environment_one_feature_state_updater_user)

    feature_state = environment.get_feature_state(feature_id=feature.id)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.patch(url, data={"enabled": True})

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_environment_admin_can_update_feature_state(
    organisation_one_project_one_environment_one,
    organisation_one_project_one_feature_one,
    environment_one_admin_user,
):
    # Given
    environment = organisation_one_project_one_environment_one
    feature = organisation_one_project_one_feature_one

    client = APIClient()
    client.force_authenticate(environment_one_admin_user)

    feature_state = environment.get_feature_state(feature_id=feature.id)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )

    # When
    response = client.patch(url, data={"enabled": True})

    # Then
    assert response.status_code == status.HTTP_200_OK
