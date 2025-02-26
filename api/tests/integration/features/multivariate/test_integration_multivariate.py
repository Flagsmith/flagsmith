import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.test import APIClient

from features.models import Feature
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_create_mv_option(client, project, mv_option_50_percent, feature):  # type: ignore[no-untyped-def]
    # Given
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 50,
    }
    # When
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"]
    assert set(data.items()).issubset(set(response.json().items()))


@pytest.mark.parametrize(
    "client, feature_id",
    [
        (lazy_fixture("admin_client"), "undefined"),
        (lazy_fixture("admin_client"), "89809"),
    ],
)
def test_cannot_create_mv_option_when_feature_id_invalid(client, feature_id, project):  # type: ignore[no-untyped-def]
    # Given
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature_id],
    )

    data = {
        "type": "unicode",
        "feature": feature_id,
        "string_value": "bigger",
        "default_percentage_allocation": 50,
    }
    # When
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_create_mv_option_when_user_is_not_owner_of_the_feature(project):  # type: ignore[no-untyped-def]
    # Given
    new_user = FFAdminUser.objects.create(email="testuser@mail.com")
    organisation = Organisation.objects.create(name="Test Org")
    new_project = Project.objects.create(name="Test project", organisation=organisation)
    feature = Feature.objects.create(
        name="New_feature",
        project=new_project,
    )
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature.id],
    )

    data = {
        "type": "unicode",
        "feature": feature.id,
        "string_value": "bigger",
        "default_percentage_allocation": 50,
    }
    client = APIClient()
    client.force_authenticate(user=new_user)
    # When
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_list_mv_option(project, mv_option_50_percent, client, feature):  # type: ignore[no-untyped-def]
    # Given
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    # When
    response = client.get(
        url,
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == mv_option_50_percent


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_creating_mv_options_with_accumulated_total_gt_100_returns_400(  # type: ignore[no-untyped-def]
    project, mv_option_50_percent, client, feature
):
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 51,
    }
    # When
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["default_percentage_allocation"] == [
        "Invalid percentage allocation"
    ]


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_update_default_percentage_allocation(  # type: ignore[no-untyped-def]
    project, mv_option_50_percent, client, feature
):
    url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[project, feature, mv_option_50_percent],
    )
    data = {
        "id": mv_option_50_percent,
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 70,
    }
    # When
    response = client.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == mv_option_50_percent
    assert set(data.items()).issubset(set(response.json().items()))


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_updating_default_percentage_allocation_that_pushes_the_total_percentage_allocation_over_100_returns_400(  # type: ignore[no-untyped-def]  # noqa: E501
    project, mv_option_50_percent, client, feature
):
    # First let's create another mv_option with 30 percent allocation
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 30,
    }
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    mv_option_30_percent = response.json()["id"]

    # Next, let's update the 30 percent mv option to 51 percent
    url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[project, feature, mv_option_30_percent],
    )
    data = {
        "id": mv_option_30_percent,
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 51,
    }
    # When
    response = client.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["default_percentage_allocation"] == [
        "Invalid percentage allocation"
    ]


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_remove_mv_option(project, mv_option_50_percent, client, feature):  # type: ignore[no-untyped-def]
    # Given
    mv_option_url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[project, feature, mv_option_50_percent],
    )

    # When
    response = client.delete(
        mv_option_url,
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # and
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    assert (
        client.get(
            url,
            content_type="application/json",
        ).json()["count"]
        == 0
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_and_update_multivariate_feature_with_2_variations_50_percent(  # type: ignore[no-untyped-def]
    project, environment, environment_api_key, client, feature
):
    """
    Specific test to reproduce issue #234 in Github
    https://github.com/Flagsmith/flagsmith/issues/234
    """
    first_mv_option_data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 50,
    }
    second_mv_option_data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "biggest",
        "default_percentage_allocation": 50,
    }
    mv_option_url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    # Create first mv option
    mv_option_response = client.post(
        mv_option_url,
        data=json.dumps(first_mv_option_data),
        content_type="application/json",
    )
    assert mv_option_response.status_code == status.HTTP_201_CREATED
    assert set(first_mv_option_data.items()).issubset(
        set(mv_option_response.json().items())
    )
    # Create second mv option
    mv_option_response = client.post(
        mv_option_url,
        data=json.dumps(second_mv_option_data),
        content_type="application/json",
    )
    assert mv_option_response.status_code == status.HTTP_201_CREATED
    assert set(second_mv_option_data.items()).issubset(
        set(mv_option_response.json().items())
    )

    # Now get the feature states for the environment so we can get the id of the
    # feature state and multivariate feature states in the given environment
    get_feature_states_url = reverse(
        "api-v1:environments:environment-featurestates-list", args=[environment_api_key]
    )
    get_feature_states_response = client.get(get_feature_states_url)
    results = get_feature_states_response.json()["results"]
    feature_state = next(filter(lambda fs: fs["feature"] == feature, results))
    feature_state_id = feature_state["id"]

    assert get_feature_states_response.status_code == status.HTTP_200_OK
    assert len(feature_state["multivariate_feature_state_values"]) == 2

    # Now we just want to try and update the feature state in the environment without
    # changing anything
    update_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state_id],
    )
    update_feature_state_data = {
        "id": feature_state_id,
        "feature_state_value": "big",
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option_id,
                "id": mv_fsv_id,
                "percentage_allocation": 50,
            }
            for mv_fsv_id, mv_option_id in [
                (mv_fsv["id"], mv_fsv["multivariate_feature_option"])
                for mv_fsv in feature_state["multivariate_feature_state_values"]
            ]
        ],
        "identity": None,
        "enabled": False,
        "feature": feature,
        "environment": environment,
        "feature_segment": None,
    }
    update_feature_state_response = client.put(
        update_url,
        data=json.dumps(update_feature_state_data),
        content_type="application/json",
    )
    assert update_feature_state_response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_modify_weight_of_2_variations_in_single_request(  # type: ignore[no-untyped-def]
    project, environment, environment_api_key, client, feature
):
    """
    Specific test to reproduce issue #807 in Github
    https://github.com/Flagsmith/flagsmith/issues/807
    """

    first_mv_option_data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 0,
    }
    second_mv_option_data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "biggest",
        "default_percentage_allocation": 100,
    }
    mv_option_url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    # Create first mv option
    mv_option_response = client.post(
        mv_option_url,
        data=json.dumps(first_mv_option_data),
        content_type="application/json",
    )
    assert mv_option_response.status_code == status.HTTP_201_CREATED
    assert set(first_mv_option_data.items()).issubset(
        set(mv_option_response.json().items())
    )
    # Create second mv option
    mv_option_response = client.post(
        mv_option_url,
        data=json.dumps(second_mv_option_data),
        content_type="application/json",
    )
    assert mv_option_response.status_code == status.HTTP_201_CREATED
    assert set(second_mv_option_data.items()).issubset(
        set(mv_option_response.json().items())
    )

    # Now get the feature states for the environment so we can get the id of the
    # feature state and multivariate feature states in the given environment
    get_feature_states_url = reverse(
        "api-v1:environments:environment-featurestates-list", args=[environment_api_key]
    )
    get_feature_states_response = client.get(get_feature_states_url)
    results = get_feature_states_response.json()["results"]
    feature_state = next(filter(lambda fs: fs["feature"] == feature, results))
    feature_state_id = feature_state["id"]

    assert get_feature_states_response.status_code == status.HTTP_200_OK
    assert len(feature_state["multivariate_feature_state_values"]) == 2

    # Now we want to switch the weighting so that the opposite variation is 100% as
    # well as adding another new variation
    update_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state_id],
    )
    update_feature_state_data = {
        "id": feature_state_id,
        "feature_state_value": "big",
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option_id,
                "id": mv_fsv_id,
                "percentage_allocation": 100 if percentage_allocation == 0 else 0,
            }
            for mv_fsv_id, mv_option_id, percentage_allocation in [
                (
                    mv_fsv["id"],
                    mv_fsv["multivariate_feature_option"],
                    mv_fsv["percentage_allocation"],
                )
                for mv_fsv in feature_state["multivariate_feature_state_values"]
            ]
        ],
        "identity": None,
        "enabled": False,
        "feature": feature,
        "environment": environment,
        "feature_segment": None,
    }
    update_feature_state_response = client.put(
        update_url,
        data=json.dumps(update_feature_state_data),
        content_type="application/json",
    )
    assert update_feature_state_response.status_code == status.HTTP_200_OK
