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


def test_retrieve_audit_log_does_not_include_change_details_for_non_update(
    admin_client: APIClient, project: int, environment: str
) -> None:
    # Given
    # we list the audit log to get an audit record that was created when
    # the environment was created in the fixture
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)

    environment_update_result = next(
        filter(
            lambda r: r["log"].startswith("New Environment created"),
            list_response.json()["results"],
        )
    )

    # When
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[environment_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    assert retrieve_response.json()["change_details"] == []


def test_retrieve_audit_log_includes_changes_when_segment_override_created_for_enabled_state(
    admin_client: APIClient,
    project: int,
    feature: int,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # First, let's create a segment override
    data = {
        "feature_segment": {"segment": segment},
        "enabled": True,
        "feature_state_value": {},
    }
    create_segment_override_url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment_api_key, feature],
    )
    create_segment_override_response = admin_client.post(
        create_segment_override_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert create_segment_override_response.status_code == status.HTTP_201_CREATED

    # Now, that should have created an audit log, let's check
    get_audit_logs_url = "%s?environment=%s" % (
        reverse("api-v1:audit-list"),
        environment,
    )
    get_audit_logs_response = admin_client.get(get_audit_logs_url)
    assert get_audit_logs_response.status_code == status.HTTP_200_OK
    results = get_audit_logs_response.json()["results"]

    # the first audit log in the list (i.e. most recent) should be the one that we want
    audit_log_id = results[0]["id"]
    get_audit_log_detail_url = reverse("api-v1:audit-detail", args=[audit_log_id])
    get_audit_log_detail_response = admin_client.get(get_audit_log_detail_url)
    assert get_audit_log_detail_response.status_code == status.HTTP_200_OK
    audit_log_details = get_audit_log_detail_response.json()

    # now let's check that we have some information in the change_details
    assert audit_log_details["change_details"] == [
        {"field": "enabled", "new": True, "old": False}
    ]


def test_retrieve_audit_log_includes_changes_when_segment_override_created_for_feature_value(
    admin_client: APIClient,
    project: int,
    feature: int,
    default_feature_value: str,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # First, let's create a segment override
    data = {
        "feature_segment": {"segment": segment},
        "feature_state_value": {"value_type": "unicode", "string_value": "foo"},
    }
    create_segment_override_url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment_api_key, feature],
    )
    create_segment_override_response = admin_client.post(
        create_segment_override_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert create_segment_override_response.status_code == status.HTTP_201_CREATED

    # Now, that should have created an audit log, let's check
    get_audit_logs_url = "%s?environment=%s" % (
        reverse("api-v1:audit-list"),
        environment,
    )
    get_audit_logs_response = admin_client.get(get_audit_logs_url)
    assert get_audit_logs_response.status_code == status.HTTP_200_OK
    results = get_audit_logs_response.json()["results"]

    # the first audit log in the list (i.e. most recent) should be the one that we want
    audit_log_id = results[0]["id"]
    get_audit_log_detail_url = reverse("api-v1:audit-detail", args=[audit_log_id])
    get_audit_log_detail_response = admin_client.get(get_audit_log_detail_url)
    assert get_audit_log_detail_response.status_code == status.HTTP_200_OK
    audit_log_details = get_audit_log_detail_response.json()

    # now let's check that we have some information in the change_details
    assert audit_log_details["change_details"] == [
        {"field": "string_value", "new": "foo", "old": default_feature_value}
    ]
