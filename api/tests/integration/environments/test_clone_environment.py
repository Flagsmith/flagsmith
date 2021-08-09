import json

from django.urls import reverse
from rest_framework import status
from tests.integration.helpers import get_env_feature_states_list_with_api

from environments.permissions.models import UserEnvironmentPermission
from features.models import FeatureSegment, FeatureState


def test_clone_environment_returns_200(
    admin_client, project, environment, environment_api_key
):
    # Given
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])

    # When
    res = admin_client.post(url, {"name": env_name})

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == env_name


def test_clone_environment_clones_feature_states_with_value(
    admin_client, project, environment, environment_api_key, feature
):

    # Firstly, create an environment and update it's feature state

    # Fetch the feature state id to update
    feature_state = FeatureState.objects.get(
        environment_id=environment, feature=feature
    )
    fs_update_url = reverse(
        "api-v1:features:featurestates-detail", args=[feature_state.id]
    )
    data = {
        "id": feature_state.id,
        "feature_state_value": "new_value",
        "enabled": False,
        "feature": feature,
        "environment": environment,
        "identity": None,
        "feature_segment": None,
    }
    admin_client.put(
        fs_update_url, data=json.dumps(data), content_type="application/json"
    )

    # Now, clone the environment
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])
    res = admin_client.post(url, {"name": env_name})

    # Then, check that the clone was successful
    assert res.status_code == status.HTTP_200_OK

    # Now, fetch the feature states of the source environment
    source_env_feature_states = get_env_feature_states_list_with_api(
        admin_client, {"environment": environment}
    )

    # Now, fetch the feature states of the clone enviroment
    clone_env_feature_states = get_env_feature_states_list_with_api(
        admin_client, {"environment": res.json()["id"]}
    )

    # Finaly, compare the responses
    assert source_env_feature_states["count"] == 1
    assert (
        source_env_feature_states["results"][0]["id"]
        != clone_env_feature_states["results"][0]["id"]
    )
    assert (
        source_env_feature_states["results"][0]["environment"]
        != clone_env_feature_states["results"][0]["environment"]
    )

    assert (
        source_env_feature_states["results"][0]["feature_state_value"]
        == clone_env_feature_states["results"][0]["feature_state_value"]
    )
    assert (
        source_env_feature_states["results"][0]["enabled"]
        == clone_env_feature_states["results"][0]["enabled"]
    )


def test_clone_environment_creates_permission_object_with_the_current_user(
    admin_user, admin_client, environment, environment_api_key
):
    # Given
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])

    # When
    res = admin_client.post(url, {"name": env_name})

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert (
        UserEnvironmentPermission.objects.filter(
            user=admin_user, environment_id=environment, admin=True
        ).count()
        == 1
    )


def test_env_clone_creates_feature_segment(
    admin_client, environment, environment_api_key, db, feature, feature_segment
):
    # Firstly, let's clone the environment
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])
    response = admin_client.post(url, {"name": env_name})

    clone_env_id = response.json()["id"]

    # Then, let's fetch feature_segment list of the clone environment
    base_url = reverse("api-v1:features:feature-segment-list")
    url = f"{base_url}?environment={clone_env_id}&feature={feature}"

    response = admin_client.get(url)
    json_response = response.json()

    # Finally, verify the structure of feature_segment
    assert json_response["count"] == 1
    assert json_response["results"][0]["environment"] == clone_env_id
    assert json_response["results"][0]["id"] != feature_segment


def test_clone_clones_segments_overrides(
    admin_client, environment, environment_api_key, feature, feature_segment, segment
):
    # Firstly, Let's override the segment in source environment
    create_url = reverse("api-v1:features:featurestates-list")
    data = {
        "feature_state_value": {
            "type": "unicode",
            "boolean_value": None,
            "integer_value": None,
            "string_value": "dumb",
        },
        "multivariate_feature_state_values": [],
        "enabled": False,
        "feature": feature,
        "environment": environment,
        "identity": None,
        "feature_segment": feature_segment,
    }
    seg_override_response = admin_client.post(
        create_url, data=json.dumps(data), content_type="application/json"
    )
    # Make sure that override was a success
    assert seg_override_response.status_code == status.HTTP_201_CREATED

    # Now, clone the environment
    env_name = "Cloned env"
    url = reverse("api-v1:environments:environment-clone", args=[environment_api_key])
    res = admin_client.post(url, {"name": env_name})

    clone_env_id = res.json()["id"]

    # Then, fetch the feature state of source environment for the feature segement
    source_env_feature_states = get_env_feature_states_list_with_api(
        admin_client,
        {
            "environment": environment,
            "feature": feature,
            "feature_segment": feature_segment,
        },
    )

    # Then, fetch the feature state of clone environment for the feature segement
    clone_feature_segment_id = FeatureSegment.objects.get(
        feature_id=feature, environment_id=clone_env_id, segment=segment
    ).id
    clone_env_feature_states = get_env_feature_states_list_with_api(
        admin_client,
        {
            "environment": clone_env_id,
            "feature": feature,
            "feature_segment": clone_feature_segment_id,
        },
    )

    assert source_env_feature_states["count"] == 1
    assert (
        source_env_feature_states["results"][0]["id"]
        != clone_env_feature_states["results"][0]["id"]
    )
    assert (
        source_env_feature_states["results"][0]["environment"]
        != clone_env_feature_states["results"][0]["environment"]
    )
    assert (
        source_env_feature_states["results"][0]["feature_state_value"]
        == clone_env_feature_states["results"][0]["feature_state_value"]
    )
    assert (
        source_env_feature_states["results"][0]["enabled"]
        == clone_env_feature_states["results"][0]["enabled"]
    )
    assert (
        clone_env_feature_states["results"][0]["feature_segment"]
        == clone_feature_segment_id
    )
