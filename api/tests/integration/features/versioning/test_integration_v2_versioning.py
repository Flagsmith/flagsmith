import json
import typing

from django.urls import reverse
from rest_framework import status


def test_v2_versioning(
    admin_client,
    environment,
    environment_api_key,
    sdk_client,
    feature,
    identity,
    identity_identifier,
    mv_feature,
):
    # First, let's get a baseline for a flags response for the environment and an identity
    # to make sure that the response before and after we enable v2 versioning is the same.
    get_environment_flags_url = reverse("api-v1:flags")
    get_identity_flags_url = "%s?identifier=%s" % (
        reverse("api-v1:sdk-identities"),
        identity_identifier,
    )

    def get_environment_flags_response_json(num_expected_flags: int) -> typing.Dict:
        _response = sdk_client.get(get_environment_flags_url)
        assert _response.status_code == status.HTTP_200_OK
        _response_json = _response.json()
        assert len(_response_json) == num_expected_flags
        return _response_json

    def get_identity_flags_response_json(num_expected_flags: int) -> typing.Dict:
        _response = sdk_client.get(get_identity_flags_url)
        assert _response.status_code == status.HTTP_200_OK
        _response_json = _response.json()
        assert len(_response_json["flags"]) == num_expected_flags
        return _response_json

    get_environment_flags_response_v1_json = get_environment_flags_response_json(2)
    get_identity_flags_response_v1_json = get_identity_flags_response_json(2)

    def verify_consistent_responses(num_expected_flags: int):
        nonlocal get_environment_flags_response_v1_json, get_identity_flags_response_v1_json
        assert (
            get_environment_flags_response_json(num_expected_flags)
            == get_environment_flags_response_v1_json
        )
        assert (
            get_identity_flags_response_json(num_expected_flags)
            == get_identity_flags_response_v1_json
        )

    # Next, let's update the environment to use v2 versioning
    environment_update_url = reverse(
        "api-v1:environments:environment-detail", args=[environment_api_key]
    )
    data = {"use_v2_feature_versioning": True}
    environment_update_response = admin_client.patch(
        environment_update_url, data=json.dumps(data), content_type="application/json"
    )
    assert environment_update_response.status_code == status.HTTP_200_OK

    # ... and let's verify that we get the same response on the flags / identities endpoints
    # before we change anything
    verify_consistent_responses(2)

    # Now, let's create a new version to add some feature states to
    environment_feature_version_list_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment, feature],
    )
    create_environment_feature_version_response = admin_client.post(
        environment_feature_version_list_url
    )
    assert (
        create_environment_feature_version_response.status_code
        == status.HTTP_201_CREATED
    )
    ef_version_sha = create_environment_feature_version_response.json()["sha"]

    # again, we should still get the same response on the flags endpoints
    verify_consistent_responses(2)

    # Now, let's add some changes to the new version but first, let's check to see that new feature states
    # have been created in the new version we created
    ef_version_featurestates_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[environment, feature, ef_version_sha],
    )
    list_ef_version_featurestates_response = admin_client.get(
        ef_version_featurestates_url
    )
    assert list_ef_version_featurestates_response.status_code == status.HTTP_200_OK
    list_ef_version_featurestates_response_json = (
        list_ef_version_featurestates_response.json()
    )
    assert len(list_ef_version_featurestates_response_json) == 1
    assert list_ef_version_featurestates_response_json[0]["feature"] == feature
