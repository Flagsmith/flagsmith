import json
import time
import typing

import pytest
from django.urls import reverse
from rest_framework import status

from tests.test_helpers import generate_segment_data

from .types import (
    GetEnvironmentFlagsResponseJSONCallable,
    GetIdentityFlagsResponseJSONCallable,
)

if typing.TYPE_CHECKING:
    from rest_framework.test import APIClient


@pytest.fixture()
def get_environment_flags_response_json(
    sdk_client: "APIClient",
) -> GetEnvironmentFlagsResponseJSONCallable:
    get_environment_flags_url = reverse("api-v1:flags")

    def _get_environment_flags_response_json(num_expected_flags: int) -> typing.Dict:
        _response = sdk_client.get(get_environment_flags_url)
        assert _response.status_code == status.HTTP_200_OK
        _response_json = _response.json()
        assert len(_response_json) == num_expected_flags
        return _response_json

    return _get_environment_flags_response_json


@pytest.fixture()
def get_identity_flags_response_json(
    sdk_client: "APIClient", identity_identifier
) -> GetIdentityFlagsResponseJSONCallable:
    identities_url = reverse("api-v1:sdk-identities")

    def _get_identity_flags_response_json(
        num_expected_flags: int, identifier: str = identity_identifier, **traits
    ) -> typing.Dict:
        traits = traits or {}
        data = {
            "identifier": identifier,
            "traits": [{"trait_key": k, "trait_value": v} for k, v in traits.items()],
        }

        _response = sdk_client.post(
            identities_url, data=json.dumps(data), content_type="application/json"
        )
        assert _response.status_code == status.HTTP_200_OK
        _response_json = _response.json()
        assert len(_response_json["flags"]) == num_expected_flags
        return _response_json

    return _get_identity_flags_response_json


@pytest.fixture()
def environment_v2_versioning(
    admin_client: "APIClient", environment: int, environment_api_key: str
) -> int:
    environment_update_url = reverse(
        "api-v1:environments:environment-enable-v2-versioning",
        args=[environment_api_key],
    )
    environment_update_response = admin_client.post(environment_update_url)
    assert environment_update_response.status_code == status.HTTP_202_ACCEPTED
    return environment


def test_v2_versioning(
    admin_client: "APIClient",
    environment: int,
    environment_api_key: str,
    sdk_client: "APIClient",
    feature: int,
    identity_with_traits_matching_segment: int,
    mv_feature: int,
    segment: int,
    get_environment_flags_response_json: GetEnvironmentFlagsResponseJSONCallable,
    get_identity_flags_response_json: GetIdentityFlagsResponseJSONCallable,
):
    # First, let's get a baseline for a flags response for the environment and an identity
    # to make sure that the response before and after we enable v2 versioning is the same.
    get_environment_flags_response_v1_json = get_environment_flags_response_json(
        num_expected_flags=2
    )
    get_identity_flags_response_v1_json = get_identity_flags_response_json(
        num_expected_flags=2
    )

    def verify_consistent_responses(num_expected_flags: int) -> None:
        new_flags_response = get_environment_flags_response_json(num_expected_flags)
        new_identities_response = get_identity_flags_response_json(num_expected_flags)

        assert new_flags_response == get_environment_flags_response_v1_json
        assert new_identities_response == get_identity_flags_response_v1_json

    # Next, let's update the environment to use v2 versioning
    environment_update_url = reverse(
        "api-v1:environments:environment-enable-v2-versioning",
        args=[environment_api_key],
    )
    environment_update_response = admin_client.post(environment_update_url)
    assert environment_update_response.status_code == status.HTTP_202_ACCEPTED

    # wait for the initial versions to have been created
    time.sleep(0.5)

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
    ef_version_uuid = create_environment_feature_version_response.json()["uuid"]

    # again, we should still get the same response on the flags endpoints
    verify_consistent_responses(num_expected_flags=2)

    # Let's check to see that a new feature state has been created in the new
    # version we created
    ef_version_featurestates_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[environment, feature, ef_version_uuid],
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
        args=[environment, feature, ef_version_uuid, new_ef_version_feature_state_id],
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

    # now, let's publish the new version and verify that we get a different response
    publish_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[environment, feature, ef_version_uuid],
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

    # finally, let's test that we can revert the v2 versioning, and we still get the
    # same response
    disable_versioning_url = reverse(
        "api-v1:environments:environment-disable-v2-versioning",
        args=[environment_api_key],
    )
    environment_update_response = admin_client.post(disable_versioning_url)
    assert environment_update_response.status_code == status.HTTP_202_ACCEPTED

    time.sleep(0.5)

    environment_flags_response_after_revert = get_environment_flags_response_json(
        num_expected_flags=2
    )
    identity_flags_response_after_revert = get_identity_flags_response_json(
        num_expected_flags=2
    )

    # Verify that the environment flags have the same state / value
    environment_flag_tuples_pre_revert = {
        (f["enabled"], f["feature_state_value"], f["feature"]["id"])
        for f in environment_flags_response_json_after_publish
    }
    environment_flag_tuples_post_revert = {
        (f["enabled"], f["feature_state_value"], f["feature"]["id"])
        for f in environment_flags_response_after_revert
    }
    assert environment_flag_tuples_pre_revert == environment_flag_tuples_post_revert

    identity_flag_tuples_pre_revert = {
        (f["enabled"], f["feature_state_value"], f["feature"]["id"])
        for f in identity_flags_response_json_after_publish["flags"]
    }
    identity_flag_tuples_post_revert = {
        (f["enabled"], f["feature_state_value"], f["feature"]["id"])
        for f in identity_flags_response_after_revert["flags"]
    }
    assert identity_flag_tuples_pre_revert == identity_flag_tuples_post_revert


def test_v2_versioning_mv_feature(
    admin_client: "APIClient",
    environment_v2_versioning: int,
    environment_api_key: str,
    sdk_client: "APIClient",
    feature: int,
    mv_feature: int,
    mv_feature_option: int,
    mv_feature_option_value: str,
    get_environment_flags_response_json: GetEnvironmentFlagsResponseJSONCallable,
    get_identity_flags_response_json: GetIdentityFlagsResponseJSONCallable,
):
    # First, let's get a baseline for a flags response for the environment and an identity
    # to make sure that the response before and after we enable v2 versioning is the same.
    get_environment_flags_response_v1_json = get_environment_flags_response_json(
        num_expected_flags=2
    )
    get_identity_flags_response_v1_json = get_identity_flags_response_json(
        num_expected_flags=2
    )

    def verify_consistent_responses(num_expected_flags: int) -> None:
        new_flags_response = get_environment_flags_response_json(num_expected_flags)
        new_identities_response = get_identity_flags_response_json(num_expected_flags)

        assert new_flags_response == get_environment_flags_response_v1_json
        assert new_identities_response == get_identity_flags_response_v1_json

    # Now, let's create a new version of the mv feature that we can update
    environment_feature_version_list_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning, mv_feature],
    )
    create_environment_feature_version_response = admin_client.post(
        environment_feature_version_list_url
    )
    assert (
        create_environment_feature_version_response.status_code
        == status.HTTP_201_CREATED
    )
    ef_version_uuid = create_environment_feature_version_response.json()["uuid"]

    verify_consistent_responses(2)

    # Let's check to see that a new feature state has been created in the new
    # version we created
    ef_version_featurestates_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[environment_v2_versioning, mv_feature, ef_version_uuid],
    )
    list_ef_version_featurestates_response = admin_client.get(
        ef_version_featurestates_url
    )
    assert list_ef_version_featurestates_response.status_code == status.HTTP_200_OK
    list_ef_version_featurestates_response_json = (
        list_ef_version_featurestates_response.json()
    )
    assert len(list_ef_version_featurestates_response_json) == 1
    new_ef_version_mv_feature_state_json = list_ef_version_featurestates_response_json[
        0
    ]
    assert new_ef_version_mv_feature_state_json["feature"] == mv_feature
    new_ef_version_feature_state_id = new_ef_version_mv_feature_state_json["id"]

    # add now let's add some changes to the new version - let's
    # change the percentages of the mv value on the feature state
    update_ef_version_feature_state_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-detail",
        args=[
            environment_v2_versioning,
            mv_feature,
            ef_version_uuid,
            new_ef_version_feature_state_id,
        ],
    )
    new_ef_version_mv_feature_state_json["multivariate_feature_state_values"][0][
        "percentage_allocation"
    ] = 100
    update_ef_version_feature_state_response = admin_client.patch(
        update_ef_version_feature_state_url,
        data=json.dumps(new_ef_version_mv_feature_state_json),
        content_type="application/json",
    )
    assert update_ef_version_feature_state_response.status_code == status.HTTP_200_OK

    # Let's verify that the responses are still the same since we haven't published
    # the new version
    verify_consistent_responses(2)

    # Now, let's publish the new version
    publish_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[environment_v2_versioning, mv_feature, ef_version_uuid],
    )
    publish_ef_version_response = admin_client.post(publish_ef_version_url)
    assert publish_ef_version_response.status_code == status.HTTP_200_OK

    # now we should see that the value of the feature state when we retrieve the flags
    # for the identity is that of the multivariate option
    identity_flags_response = get_identity_flags_response_json(2)
    mv_flag = next(
        filter(
            lambda f: f["feature"]["id"] == mv_feature, identity_flags_response["flags"]
        )
    )
    assert mv_flag["feature_state_value"] == mv_feature_option_value


def test_v2_versioning_multiple_segment_overrides(
    admin_client: "APIClient",
    environment_v2_versioning: int,
    environment_api_key: str,
    sdk_client: "APIClient",
    project: int,
    feature: int,
    get_environment_flags_response_json: GetEnvironmentFlagsResponseJSONCallable,
    get_identity_flags_response_json: GetIdentityFlagsResponseJSONCallable,
):
    # Firstly, let's define an identity and their traits
    identifier = "identity"
    trait_key_1 = "trait_key_1"
    trait_value_1 = "trait_value_1"
    trait_key_2 = "trait_key_2"
    trait_value_2 = "trait_value_2"

    # now, let's create 2 segments which both match this identity
    create_segment_url = reverse(
        "api-v1:projects:project-segments-list", args=[project]
    )
    segment_1_response = admin_client.post(
        create_segment_url,
        data=json.dumps(
            generate_segment_data(
                segment_name="segment_1",
                project_id=project,
                condition_tuples=[(trait_key_1, "EQUAL", trait_value_1)],
            )
        ),
        content_type="application/json",
    )
    segment_1_id = segment_1_response.json()["id"]

    segment_2_response = admin_client.post(
        create_segment_url,
        data=json.dumps(
            generate_segment_data(
                segment_name="segment_2",
                project_id=project,
                condition_tuples=[(trait_key_2, "EQUAL", trait_value_2)],
            )
        ),
        content_type="application/json",
    )
    segment_2_id = segment_2_response.json()["id"]

    # Now, let's create a new version to add some segment overrides to
    environment_feature_version_list_url = reverse(
        "api-v1:versioning:environment-feature-versions-list",
        args=[environment_v2_versioning, feature],
    )
    create_environment_feature_version_response = admin_client.post(
        environment_feature_version_list_url
    )
    assert (
        create_environment_feature_version_response.status_code
        == status.HTTP_201_CREATED
    )
    ef_version_uuid = create_environment_feature_version_response.json()["uuid"]

    # and let's add an override for each of the segments
    ef_version_featurestates_url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[environment_v2_versioning, feature, ef_version_uuid],
    )

    segment_1_override_value = "segment_1_override"
    segment_2_override_value = "segment_2_override"

    feature_segment_id_priority_pairs = []

    for segment_id, feature_state_value in (
        (segment_1_id, segment_1_override_value),
        (segment_2_id, segment_2_override_value),
    ):
        create_ef_version_segment_override_response = admin_client.post(
            ef_version_featurestates_url,
            data=json.dumps(
                {
                    "enabled": True,
                    "feature_state_value": {
                        "string_value": feature_state_value,
                        "value_type": "unicode",
                    },
                    "feature_segment": {"segment": segment_id},
                }
            ),
            content_type="application/json",
        )
        assert (
            create_ef_version_segment_override_response.status_code
            == status.HTTP_201_CREATED
        )
        create_segment_override_response_json = (
            create_ef_version_segment_override_response.json()
        )
        feature_segment_data = create_segment_override_response_json["feature_segment"]
        feature_segment_id_priority_pairs.append(
            (feature_segment_data["id"], feature_segment_data["priority"])
        )

    # now, let's publish the new version
    publish_ef_version_url = reverse(
        "api-v1:versioning:environment-feature-versions-publish",
        args=[environment_v2_versioning, feature, ef_version_uuid],
    )
    publish_ef_version_response = admin_client.post(publish_ef_version_url)
    assert publish_ef_version_response.status_code == status.HTTP_200_OK

    # now, let's get the flags for the identity
    identity_flags_response_json = get_identity_flags_response_json(
        num_expected_flags=1,
        identifier=identifier,
        **{trait_key_1: trait_value_1, trait_key_2: trait_value_2},
    )

    # and verify that we get the value from the override for segment 1,
    # since that was added first, and should have a higher priority
    assert (
        identity_flags_response_json["flags"][0]["feature_state_value"]
        == segment_1_override_value
    )

    # now lets re-order the segment overrides
    re_order_segment_overrides_url = reverse(
        "api-v1:features:feature-segment-update-priorities"
    )
    data = [
        {
            "id": feature_segment_id_priority_pairs[1][0],
            "priority": feature_segment_id_priority_pairs[0][1],
        },
        {
            "id": feature_segment_id_priority_pairs[0][0],
            "priority": feature_segment_id_priority_pairs[1][1],
        },
    ]
    reorder_segment_overrides_response = admin_client.post(
        re_order_segment_overrides_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert reorder_segment_overrides_response.status_code == status.HTTP_200_OK

    # now, let's get the flags for the identity
    identity_flags_response_json = get_identity_flags_response_json(
        num_expected_flags=1,
        identifier=identifier,
        **{trait_key_1: trait_value_1, trait_key_2: trait_value_2},
    )

    # and verify that we get the value from the override for segment 2,
    # since we just re-ordered the overrides
    assert (
        identity_flags_response_json["flags"][0]["feature_state_value"]
        == segment_2_override_value
    )

    # and finally, let's create a new version to ensure that it works as we
    # expect
    second_create_environment_feature_version_response = admin_client.post(
        environment_feature_version_list_url
    )
    assert (
        second_create_environment_feature_version_response.status_code
        == status.HTTP_201_CREATED
    )


def test_v2_versioning_carries_existing_segment_overrides_across(
    environment: int,
    environment_api_key: str,
    admin_client: "APIClient",
    segment: int,
    feature: int,
    feature_segment: int,
    segment_featurestate: int,
) -> None:
    """
    This is a specific test to reproduce an issue found in testing where, after
    enabling v2 versioning, feature segments were not being returned via the
    API.
    """
    # Given
    feature_segments_list_url = "%s?feature=%d&environment=%d" % (
        reverse("api-v1:features:feature-segment-list"),
        feature,
        environment,
    )

    # Firstly, let's check the response to the feature segments list endpoint
    # before we enable v2 versioning.
    feature_segment_list_pre_migrate_response = admin_client.get(
        feature_segments_list_url
    )
    feature_segments_list_response_pre_migrate_json = (
        feature_segment_list_pre_migrate_response.json()
    )
    assert feature_segments_list_response_pre_migrate_json["count"] == 1
    assert (
        feature_segments_list_response_pre_migrate_json["results"][0]["id"]
        == feature_segment
    )

    # Now, let's enable v2 versioning.
    enable_v2_versioning_url = reverse(
        "api-v1:environments:environment-enable-v2-versioning",
        args=[environment_api_key],
    )
    assert (
        admin_client.post(enable_v2_versioning_url).status_code
        == status.HTTP_202_ACCEPTED
    )

    # and let's check the response to the feature segments endpoint after enabling v2 versioning
    feature_segment_list_post_migrate_response = admin_client.get(
        feature_segments_list_url
    )
    feature_segment_list_post_migrate_response_json = (
        feature_segment_list_post_migrate_response.json()
    )
    assert feature_segment_list_post_migrate_response_json["count"] == 1
    assert (
        feature_segment_list_post_migrate_response_json["results"][0]["id"]
        == feature_segment
    )
