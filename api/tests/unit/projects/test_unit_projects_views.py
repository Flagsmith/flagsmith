import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from features.models import Feature
from projects.models import Project
from segments.models import Segment


@pytest.mark.parametrize(
    "client",
    (lazy_fixture("admin_client"), lazy_fixture("admin_master_api_key_client")),
)
def test_get_project_list_data(client, organisation):
    # Given
    list_url = reverse("api-v1:projects:project-list")

    project_name = "Test project"
    hide_disabled_flags = False
    enable_dynamo_db = False
    prevent_flag_defaults = True
    enable_realtime_updates = False
    only_allow_lower_case_feature_names = True

    Project.objects.create(
        name=project_name,
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
    assert response.json()[0]["name"] == project_name
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
    "client",
    (lazy_fixture("admin_client"), lazy_fixture("admin_master_api_key_client")),
)
def test_get_project_data_by_id(client, organisation, project):
    # Given
    url = reverse("api-v1:projects:project-detail", args=[project.id])

    num_features = 5
    num_segments = 7

    for i in range(num_features):
        Feature.objects.create(name=f"feature_{i}", project=project)

    for i in range(num_segments):
        Segment.objects.create(name=f"feature_{i}", project=project)

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == project.name
    assert response.json()["max_segments_allowed"] == 100
    assert response.json()["max_features_allowed"] == 400
    assert response.json()["max_segment_overrides_allowed"] == 100
    assert response.json()["total_features"] == num_features
    assert response.json()["total_segments"] == num_segments
