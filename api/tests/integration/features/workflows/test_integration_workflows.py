import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_4_eyes_workflow(
    admin_client,
    sdk_client,
    organisation,
    project,
    environment_api_key,
    environment,
    default_feature_value,
    feature,
    registered_org_admin_user_email,
    registered_org_admin_user,
    settings,
):
    settings.CACHE_FLAGS_SECONDS = 0  # ensure no caching of flags

    # First, let's get the feature state for the given feature in the given environment
    get_environment_feature_states_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=(environment_api_key,),
    )
    get_feature_states_response = admin_client.get(get_environment_feature_states_url)
    assert get_feature_states_response.status_code == status.HTTP_200_OK
    response_json = get_feature_states_response.json()
    assert response_json["count"] == 1
    feature_state_id = response_json["results"][0]["id"]

    # Now let's verify the responses from the SDK flags & identities endpoint before
    # we create a CR
    flags_url = reverse("api-v1:flags")
    identities_url = "%s?identifier=some-identity" % reverse("api-v1:sdk-identities")
    pre_cr_responses = {}
    for url in (flags_url, identities_url):
        response = sdk_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        flags = response.json() if url == flags_url else response.json()["flags"]
        assert len(flags) == 1
        assert flags[0]["enabled"] is False
        assert flags[0]["feature_state_value"] == default_feature_value
        pre_cr_responses[url] = flags

    # Now let's create a CR and add a required approval for the registered user
    create_cr_url = reverse(
        "api-v1:environments:environment-featurestates-create-change-request",
        args=(environment_api_key, feature_state_id),
    )
    registered_user_id, registered_user_token = registered_org_admin_user
    data = {
        "title": "My Change Request",
        "from_feature_state": feature_state_id,
        "to_feature_state": {
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foobar"},
        },
        "approvals": [{"user": registered_user_id, "required": True}],
    }
    create_cr_response = admin_client.post(
        create_cr_url, data=json.dumps(data), content_type="application/json"
    )
    assert create_cr_response.status_code == status.HTTP_201_CREATED
    create_cr_response_json = create_cr_response.json()
    change_request_id = create_cr_response_json["id"]

    # Now, let's verify that nothing has changed with the flags & identities responses
    for url in (flags_url, identities_url):
        response = sdk_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        flags = response.json() if url == flags_url else response.json()["flags"]
        assert flags == pre_cr_responses[url]

    # Now, before we approve the CR, let's verify that it's not possible to commit
    # without approval
    commit_cr_url = reverse(
        "api-v1:features:workflows:change-requests-commit", args=(change_request_id,)
    )
    invalid_commit_cr_response = admin_client.post(commit_cr_url)
    assert invalid_commit_cr_response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        invalid_commit_cr_response.json()["detail"]
        == "Change request has not been approved by all required approvers."
    )

    # Now, let's approve the CR and commit it
    approve_cr_url = reverse(
        "api-v1:features:workflows:change-requests-approve", args=(change_request_id,)
    )
    registered_user_client = APIClient()
    registered_user_client.credentials(
        HTTP_AUTHORIZATION=f"Token {registered_user_token}"
    )
    approve_cr_response = registered_user_client.post(approve_cr_url)
    assert approve_cr_response.status_code == status.HTTP_200_OK

    commit_cr_response = admin_client.post(commit_cr_url)
    assert commit_cr_response.status_code == status.HTTP_200_OK

    # Now, let's verify that the flags & identities responses correctly reflect the
    # change from the CR
    for url in (flags_url, identities_url):
        response = sdk_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        flags = response.json() if url == flags_url else response.json()["flags"]
        assert len(flags) == 1
        assert flags[0]["enabled"] is True  # new value
        assert flags[0]["feature_state_value"] == "foobar"  # new value
