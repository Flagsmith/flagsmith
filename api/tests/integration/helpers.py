import json

from django.urls import reverse
from django.utils.http import urlencode
from rest_framework.test import APIClient

from features.feature_types import STANDARD
from features.value_types import STRING


def create_feature_with_api(
    client: APIClient,
    project_id: int,
    feature_name: str,
    initial_value: str,
    feature_type: str = STANDARD,
) -> int:
    """
    Create a feature against the API using the provided test client.

    :param client: DRF api client to use to make the request
    :param feature_name: Name of the feature to create
    :param initial_value: Initial value to give the feature
    :param multivariate_options: List of 2-tuples containing the string value and percentage allocation
    :return: id of the created feature
    """
    create_feature_url = reverse(
        "api-v1:projects:project-features-list", args=[project_id]
    )
    create_standard_feature_data = {
        "name": feature_name,
        "type": feature_type,
        "initial_value": initial_value,
        "default_enabled": True,
    }
    create_standard_feature_response = client.post(
        create_feature_url,
        data=json.dumps(create_standard_feature_data),
        content_type="application/json",
    )
    return create_standard_feature_response.json()["id"]


def create_mv_option_with_api(
    client: APIClient,
    project_id: int,
    feature_id: str,
    default_percentage_allocation: float,
    value: str,
) -> int:
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project_id, feature_id],
    )
    data = {
        "type": STRING,
        "feature": feature_id,
        "string_value": value,
        "default_percentage_allocation": default_percentage_allocation,
    }
    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    return response.json()["id"]


def get_env_feature_states_list_with_api(client: APIClient, query_params: dict) -> dict:
    """
    Returns feature states using the provided test client.

    :param client: DRF api client to use to make the request
    :param query_params: A Mapping object used as query params for filtering

    """
    url = reverse("api-v1:features:featurestates-list")
    response = get_json_response(client, url, query_params)
    return response


def get_feature_segement_list_with_api(client: APIClient, query_params: dict) -> dict:
    """
    Returns feature segments using the provided test client.

    :param client: DRF api client to use to make the request
    :param query_params: A Mapping object used as query params for filtering

    """

    url = reverse("api-v1:features:feature-segment-list")
    return get_json_response(client, url, query_params)


def get_json_response(client: APIClient, url: str, query_params: dict) -> dict:
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    return client.get(url).json()
