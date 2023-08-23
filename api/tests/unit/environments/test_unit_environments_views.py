from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment


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
