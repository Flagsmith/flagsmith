import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_audit_logs_only_makes_two_queries(
    admin_client,
    project,
    environment,
    feature,
    feature_state,
    django_assert_num_queries,
):
    url = reverse("api-v1:audit-list")

    with django_assert_num_queries(2):
        res = admin_client.get(url, {"project": project})

    assert res.status_code == status.HTTP_200_OK
    assert res.json()["count"] == 3


def test_retrieve_audit_log_for_environment_change(
    admin_client: APIClient,
    project: int,
    environment_api_key: str,
    environment_name: str,
    environment: int,
) -> None:
    # Given
    # we update the environment
    update_environment_url = reverse(
        "api-v1:environments:environment-detail",
        args=[environment_api_key],
    )
    new_name = "some new name!"
    data = {"name": new_name}
    admin_client.patch(
        update_environment_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)

    # When
    # We retrieve the record directly where we updated the environment
    environment_update_result = next(
        filter(
            lambda r: r["log"].startswith("Environment updated"),
            list_response.json()["results"],
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[environment_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "name"
    assert retrieve_response_json["change_details"][0]["new"] == new_name
    assert retrieve_response_json["change_details"][0]["old"] == environment_name


def test_retrieve_audit_log_for_feature_state_enabled_change(
    admin_client: APIClient,
    environment_api_key: str,
    environment: int,
    feature: int,
    feature_state: int,
) -> None:
    # Given
    # we update the state and value of a feature in an environment
    update_feature_state_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state],
    )
    data = {"enabled": True}
    admin_client.patch(
        update_feature_state_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)
    list_results = list_response.json()["results"]

    # When
    # We retrieve the records directly where we updated the feature state
    flag_state_update_result = next(
        filter(
            lambda r: r["log"].startswith("Flag state updated"),
            list_results,
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[flag_state_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "enabled"
    assert retrieve_response_json["change_details"][0]["new"] is True
    assert retrieve_response_json["change_details"][0]["old"] is False


def test_retrieve_audit_log_for_feature_state_value_change(
    admin_client: APIClient,
    environment_api_key: str,
    environment: int,
    feature: int,
    feature_state: int,
    default_feature_value: str,
) -> None:
    # Given
    # we update the state and value of a feature in an environment
    new_value = "foobar"
    update_feature_state_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state],
    )
    data = {"feature_state_value": new_value}
    admin_client.patch(
        update_feature_state_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)
    list_results = list_response.json()["results"]

    # When
    # We retrieve the records directly where we updated the feature state
    flag_state_update_result = next(
        filter(
            lambda r: r["log"].startswith("Remote config value updated"),
            list_results,
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[flag_state_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "string_value"
    assert retrieve_response_json["change_details"][0]["new"] == new_value
    assert retrieve_response_json["change_details"][0]["old"] == default_feature_value
