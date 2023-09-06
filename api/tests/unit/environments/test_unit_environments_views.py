from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from projects.permissions import CREATE_ENVIRONMENT


def test_retrieve_environment(
    admin_client: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    assert response_json["id"] == environment.id
    assert response_json["name"] == environment.name
    assert response_json["project"] == environment.project_id
    assert response_json["api_key"] == environment.api_key
    assert response_json["allow_client_traits"] == environment.allow_client_traits
    assert response_json["banner_colour"] == environment.banner_colour
    assert response_json["banner_text"] == environment.banner_text
    assert response_json["description"] == environment.description
    assert response_json["hide_disabled_flags"] == environment.hide_disabled_flags
    assert response_json["hide_sensitive_data"] == environment.hide_sensitive_data
    assert response_json["metadata"] == []
    assert (
        response_json["minimum_change_request_approvals"]
        == environment.minimum_change_request_approvals
    )
    assert (
        response_json["total_segment_overrides"] == environment.feature_segments.count()
    )
    assert (
        response_json["use_identity_composite_key_for_hashing"]
        == environment.use_identity_composite_key_for_hashing
    )
    assert (
        response_json["use_mv_v2_evaluation"]
        == environment.use_identity_composite_key_for_hashing
    )


def test_can_clone_environment_with_create_environment_permission(
    test_user,
    test_user_client,
    environment,
    user_project_permission,
):
    # Given
    env_name = "Cloned env"
    user_project_permission.permissions.add(CREATE_ENVIRONMENT)

    url = reverse("api-v1:environments:environment-clone", args=[environment.api_key])

    # When
    response = test_user_client.post(url, {"name": env_name})

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_cannot_enable_v2_versioning_for_environment_already_enabled(
    environment_v2_versioning: Environment,
    admin_client: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-enable-v2-versioning",
        args=[environment_v2_versioning.api_key],
    )

    mock_enable_v2_versioning = mocker.patch("environments.views.enable_v2_versioning")

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Environment already using v2 versioning."}

    mock_enable_v2_versioning.delay.assert_not_called()
