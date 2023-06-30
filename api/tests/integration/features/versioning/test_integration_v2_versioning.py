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
    identity_with_traits_matching_segment,
    identity_identifier,
    mv_feature,
    segment,
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

    get_environment_flags_response_v1_json = get_environment_flags_response_json(
        num_expected_flags=2
    )
    get_identity_flags_response_v1_json = get_identity_flags_response_json(
        num_expected_flags=2
    )

    def verify_consistent_responses(num_expected_flags: int):
        nonlocal get_environment_flags_response_v1_json, get_identity_flags_response_v1_json
        new_flags_response = get_environment_flags_response_json(num_expected_flags)
        new_identities_response = get_identity_flags_response_json(num_expected_flags)

        assert new_flags_response == get_environment_flags_response_v1_json
        assert new_identities_response == get_identity_flags_response_v1_json

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
    verify_consistent_responses(num_expected_flags=2)

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
    verify_consistent_responses(num_expected_flags=2)

    # Let's check to see that a new feature state has been created in the new
    # version we created
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
    new_ef_version_feature_state_id = list_ef_version_featurestates_response_json[0][
        "id"
    ]

    # add now let's add some changes to the new version
    # let's change the value of the feature state
    update_ef_version_feature_state_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[environment, feature, ef_version_sha, new_ef_version_feature_state_id],
    )
    update_ef_version_feature_state_response = admin_client.patch(
        update_ef_version_feature_state_url,
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {
                    "string_value": "v2-value",
                    "value_type": "unicode",
                },
            }
        ),
        content_type="application/json",
    )
    assert update_ef_version_feature_state_response.status_code == status.HTTP_200_OK

    # and create a segment override
    create_ef_version_segment_override_response = admin_client.post(
        ef_version_featurestates_url,
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {
                    "string_value": "v2-segment-override-value",
                    "value_type": "unicode",
                },
                "feature_segment": {"segment": segment},
            }
        ),
        content_type="application/json",
    )
    assert (
        create_ef_version_segment_override_response.status_code
        == status.HTTP_201_CREATED
    )

    # since we still haven't published the new version, the flags responses should
    # still behave the same
    verify_consistent_responses(num_expected_flags=2)

    # finally, let's publish the new version and verify that we get a different response
    publish_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[environment, feature, ef_version_sha],
    )
    publish_ef_version_response = admin_client.post(publish_ef_version_url)
    assert publish_ef_version_response.status_code == status.HTTP_200_OK

    # now, we expect the values to have been updated
    environment_flags_response_json_after_publish = get_environment_flags_response_json(
        num_expected_flags=2
    )
    # let's verify that the standard feature is now enabled and has the value we gave it
    # in the new version
    environment_response_standard_feature_data = next(
        filter(
            lambda flag: flag["feature"]["id"] == feature,
            environment_flags_response_json_after_publish,
        )
    )
    assert environment_response_standard_feature_data["enabled"] is True
    assert (
        environment_response_standard_feature_data["feature_state_value"] == "v2-value"
    )

    # and that it is overridden by the segment override for the identity
    # TODO:
    #  - identities logic is still not using versioning, needs updating.
    identity_flags_response_json_after_publish = get_identity_flags_response_json(
        num_expected_flags=2
    )
    identity_response_standard_feature_data = next(
        filter(
            lambda flag: flag["feature"]["id"] == feature,
            identity_flags_response_json_after_publish["flags"],
        )
    )
    assert identity_response_standard_feature_data["enabled"] is True
    assert (
        identity_response_standard_feature_data["feature_state_value"]
        == "v2-segment-override-value"
    )
