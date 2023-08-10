import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from projects.models import Project

list_url = reverse("api-v1:projects:project-list")
PROJECT_NAME = "Test project"


@pytest.mark.parametrize(
    "client", (lazy_fixture("admin_client"), lazy_fixture("master_api_key_client"))
)
def test_get_project_list_data(client, organisation):
    # Given
    hide_disabled_flags = False
    enable_dynamo_db = False
    prevent_flag_defaults = True
    enable_realtime_updates = False
    only_allow_lower_case_feature_names = True

    Project.objects.create(
        name=PROJECT_NAME,
        organisation=organisation,
        hide_disabled_flags=hide_disabled_flags,
        enable_dynamo_db=enable_dynamo_db,
        prevent_flag_defaults=prevent_flag_defaults,
        enable_realtime_updates=enable_realtime_updates,
        only_allow_lower_case_feature_names=only_allow_lower_case_feature_names,
    )

    # When
    response = client.get(list_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == PROJECT_NAME
    assert response.json()[0]["hide_disabled_flags"] is hide_disabled_flags
    assert response.json()[0]["enable_dynamo_db"] is enable_dynamo_db
    assert response.json()[0]["prevent_flag_defaults"] is prevent_flag_defaults
    assert response.json()[0]["enable_realtime_updates"] is enable_realtime_updates
    assert (
        response.json()[0]["only_allow_lower_case_feature_names"]
        is only_allow_lower_case_feature_names
    )
    assert "max_segments_allowed" not in response.json()[0].keys()
    assert "max_features_allowed" not in response.json()[0].keys()
    assert "max_segment_overrides_allowed" not in response.json()[0].keys()
    assert "total_features" not in response.json()[0].keys()
    assert "total_segments" not in response.json()[0].keys()


@pytest.mark.parametrize(
    "client", (lazy_fixture("admin_client"), lazy_fixture("master_api_key_client"))
)
def test_get_project_data_by_id(client, organisation):
    # Given
    project = Project.objects.create(
        name=PROJECT_NAME,
        organisation=organisation,
    )
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == PROJECT_NAME
    assert response.json()["max_segments_allowed"] == 100
    assert response.json()["max_features_allowed"] == 400
    assert response.json()["max_segment_overrides_allowed"] == 100
    assert response.json()["total_features"] == 0
    assert response.json()["total_segments"] == 0
