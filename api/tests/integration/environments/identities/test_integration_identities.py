import hashlib
import json
from typing import Any, Generator
from unittest import mock

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_types import MULTIVARIATE
from tests.integration.helpers import (
    create_feature_with_api,
    create_mv_option_with_api,
)

variant_1_value = "variant-1-value"
variant_2_value = "variant-2-value"
control_value = "control"

variant_1_percentage_allocation = 20
variant_2_percentage_allocation = 30
total_variance_percentage = (
    variant_1_percentage_allocation + variant_2_percentage_allocation
)


# mock the returned percentage for the identity to simulate them falling into each of
# the percentage allocation brackets for the feature variants
@pytest.mark.parametrize(
    "hashed_percentage, expected_mv_value",
    (
        (variant_1_percentage_allocation / 100 - 0.01, variant_1_value),
        (total_variance_percentage / 100 - 0.01, variant_2_value),
        (total_variance_percentage / 100 + 0.01, control_value),
    ),
)
@mock.patch("features.models.get_hashed_percentage_for_object_ids")
def test_get_feature_states_for_identity(
    mock_get_hashed_percentage_value,
    hashed_percentage,
    expected_mv_value,
    sdk_client,
    admin_client,
    project,
    environment_api_key,
    environment,
    identity,
    identity_identifier,
):
    # Firstly, let's create some features to use
    # one standard feature
    standard_feature_initial_value = "control"
    standard_feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="standard_feature",
        initial_value=standard_feature_initial_value,
    )

    # and one multivariate feature
    multivariate_feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="multivariate_feature",
        initial_value=control_value,
        feature_type=MULTIVARIATE,
    )
    # With two mv options
    create_mv_option_with_api(
        admin_client,
        project,
        multivariate_feature_id,
        variant_1_percentage_allocation,
        variant_1_value,
    )
    create_mv_option_with_api(
        admin_client,
        project,
        multivariate_feature_id,
        variant_2_percentage_allocation,
        variant_2_value,
    )

    # Now, when we mock the hashed percentage that the user gets
    # to avoid the randomness factor
    mock_get_hashed_percentage_value.return_value = hashed_percentage

    # and request the flags for the identity
    base_identity_flags_url = reverse("api-v1:sdk-identities")
    identity_flags_url = f"{base_identity_flags_url}?identifier={identity_identifier}"
    identity_response_1 = sdk_client.get(identity_flags_url)

    # Then, we get a result for both of the features we created
    assert identity_response_1.status_code == status.HTTP_200_OK
    identity_response_json = identity_response_1.json()
    assert len(identity_response_json["flags"]) == 2

    # and the correct values are returned for the features
    values_dict = {
        flag["feature"]["id"]: flag["feature_state_value"]
        for flag in identity_response_json["flags"]
    }
    assert values_dict[standard_feature_id] == standard_feature_initial_value
    assert values_dict[multivariate_feature_id] == expected_mv_value

    # Now, let's change the percentage allocations on the mv options
    # first, we need to get the feature state id for the feature in the given
    # environment
    feature_state_id = next(
        filter(
            lambda flag: flag["feature"]["id"] == multivariate_feature_id,
            identity_response_json["flags"],
        )
    )["id"]

    # now let's get the existing data for the feature state so we can alter it and
    # then PUT it back
    feature_state_detail_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state_id],
    )
    retrieve_feature_state_response = admin_client.get(feature_state_detail_url)
    feature_state_data = retrieve_feature_state_response.json()

    # now let's amend the data so that all identities should receive variant 2
    mv_values = feature_state_data["multivariate_feature_state_values"]
    mv_values[0]["percentage_allocation"] = 0
    mv_values[1]["percentage_allocation"] = 100

    # and PUT the data back
    update_feature_state_response = admin_client.put(
        feature_state_detail_url,
        data=json.dumps(feature_state_data),
        content_type="application/json",
    )
    assert update_feature_state_response.status_code == status.HTTP_200_OK

    # Then when we get the flags for an identity, the multivariate feature returns the
    # value of the 2nd variate
    identity_response_2 = sdk_client.get(identity_flags_url)
    values_dict = {
        flag["feature"]["id"]: flag["feature_state_value"]
        for flag in identity_response_2.json()["flags"]
    }
    assert values_dict[multivariate_feature_id] == variant_2_value


def test_get_feature_states_for_identity_only_makes_one_query_to_get_mv_feature_states(
    sdk_client,
    admin_client,
    project,
    environment,
    identity,
    identity_identifier,
    django_assert_num_queries,
):
    # Firstly, let's create some features to use
    for i in range(2):
        feature_id = create_feature_with_api(
            client=admin_client,
            project_id=project,
            feature_name=f"multivariate_feature_{i}",
            initial_value=control_value,
            feature_type=MULTIVARIATE,
        )
        create_mv_option_with_api(
            admin_client,
            project,
            feature_id,
            variant_1_percentage_allocation,
            variant_1_value,
        )
        create_mv_option_with_api(
            admin_client,
            project,
            feature_id,
            variant_2_percentage_allocation,
            variant_2_value,
        )

    # When we make a request to get the flags for the identity, 6 queries are made
    # TODO: can we reduce the number of queries?!
    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity_identifier}"

    with django_assert_num_queries(6):
        first_identity_response = sdk_client.get(url)

    # Now, if we add another feature
    feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="another_multivariate_feature",
        initial_value=control_value,
        feature_type=MULTIVARIATE,
    )
    create_mv_option_with_api(
        admin_client,
        project,
        feature_id,
        variant_1_percentage_allocation,
        variant_1_value,
    )
    create_mv_option_with_api(
        admin_client,
        project,
        feature_id,
        variant_2_percentage_allocation,
        variant_2_value,
    )

    # Then one fewer db queries are made (since the environment is now cached)
    with django_assert_num_queries(5):
        second_identity_response = sdk_client.get(url)

    # Finally, we check that the requests were successful and we got the correct number
    # of flags in each case
    assert first_identity_response.status_code == status.HTTP_200_OK
    assert second_identity_response.status_code == status.HTTP_200_OK

    first_identity_response_json = first_identity_response.json()
    assert len(first_identity_response_json["flags"]) == 2

    second_identity_response_json = second_identity_response.json()
    assert len(second_identity_response_json["flags"]) == 3


@pytest.fixture
def existing_identity_identifier_data(
    identity_identifier: str,
    identity: int,
) -> dict[str, Any]:
    return {"identifier": identity_identifier}


@pytest.fixture
def transient_identifier(
    segment_condition_property: str,
    segment_condition_value: str,
) -> Generator[str, None, None]:
    return hashlib.sha256(
        f"avalue_a{segment_condition_property}{segment_condition_value}".encode()
    ).hexdigest()


@pytest.mark.parametrize(
    "transient_data",
    [
        pytest.param({"transient": True}, id="with-transient-true"),
        pytest.param({"transient": False}, id="with-transient-false"),
        pytest.param({}, id="missing-transient"),
    ],
)
@pytest.mark.parametrize(
    "identifier_data,expected_identifier",
    [
        pytest.param(
            lazy_fixture("existing_identity_identifier_data"),
            lazy_fixture("identity_identifier"),
            id="existing-identifier",
        ),
        pytest.param({"identifier": "unseen"}, "unseen", id="new-identifier"),
        pytest.param(
            {"identifier": ""},
            lazy_fixture("transient_identifier"),
            id="blank-identifier",
        ),
        pytest.param(
            {"identifier": None},
            lazy_fixture("transient_identifier"),
            id="null-identifier",
        ),
        pytest.param({}, lazy_fixture("transient_identifier"), id="missing-identifier"),
    ],
)
def test_get_feature_states_for_identity__segment_match_expected(
    sdk_client: APIClient,
    feature: int,
    segment: int,
    segment_condition_property: str,
    segment_condition_value: str,
    segment_featurestate: int,
    identifier_data: dict[str, Any],
    transient_data: dict[str, Any],
    expected_identifier: str,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # When
    # flags are requested for a new transient identity
    # that matches the segment
    response = sdk_client.post(
        url,
        data=json.dumps(
            {
                **identifier_data,
                **transient_data,
                "traits": [
                    {
                        "trait_key": segment_condition_property,
                        "trait_value": segment_condition_value,
                    },
                    {"trait_key": "a", "trait_value": "value_a"},
                    {"trait_key": "c", "trait_value": None},
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["identifier"] == expected_identifier
    assert (
        flag_data := next(
            (
                flag
                for flag in response_json["flags"]
                if flag["feature"]["id"] == feature
            ),
            None,
        )
    )
    assert flag_data["enabled"] is True
    assert flag_data["feature_state_value"] == "segment override"


def test_get_feature_states_for_identity__empty_traits__random_identifier_expected(
    sdk_client: APIClient,
    environment: int,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # When
    response_1 = sdk_client.post(
        url,
        data=json.dumps({"traits": []}),
        content_type="application/json",
    )
    response_2 = sdk_client.post(
        url,
        data=json.dumps({"traits": []}),
        content_type="application/json",
    )

    # Then
    assert response_1.json()["identifier"] != response_2.json()["identifier"]


def test_get_feature_states_for_identity__transient_trait__segment_match_expected(
    sdk_client: APIClient,
    feature: int,
    segment: int,
    segment_condition_property: str,
    segment_condition_value: str,
    segment_featurestate: int,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # When
    # flags are requested for a new identity
    # that matches the segment
    # with a transient trait
    response = sdk_client.post(
        url,
        data=json.dumps(
            {
                "identifier": "unseen",
                "traits": [
                    {
                        "trait_key": segment_condition_property,
                        "trait_value": segment_condition_value,
                        "transient": True,
                    },
                    {
                        "trait_key": "persistent",
                        "trait_value": "trait value",
                    },
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["traits"] == [
        {
            "id": mock.ANY,
            "trait_key": segment_condition_property,
            "trait_value": segment_condition_value,
            "transient": True,
        },
        {
            "id": mock.ANY,
            "trait_key": "persistent",
            "trait_value": "trait value",
            "transient": False,
        },
    ]
    assert (
        flag_data := next(
            (
                flag
                for flag in response_json["flags"]
                if flag["feature"]["id"] == feature
            ),
            None,
        )
    )
    assert flag_data["enabled"] is True
    assert flag_data["feature_state_value"] == "segment override"


def test_get_feature_states_for_identity__transient_trait__existing_identity__return_expected(
    sdk_client: APIClient,
    identity_identifier: str,
    identity: int,
) -> None:
    # Given
    url = reverse("api-v1:sdk-identities")

    # When
    # flags are requested for an existing identity
    # with a transient trait
    response = sdk_client.post(
        url,
        data=json.dumps(
            {
                "identifier": identity_identifier,
                "traits": [
                    {
                        "trait_key": "transient",
                        "trait_value": "trait value",
                        "transient": True,
                    },
                    {
                        "trait_key": "persistent",
                        "trait_value": "trait value",
                    },
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["traits"] == [
        {
            "id": mock.ANY,
            "trait_key": "persistent",
            "trait_value": "trait value",
            "transient": False,
        },
        {
            "id": mock.ANY,
            "trait_key": "transient",
            "trait_value": "trait value",
            "transient": True,
        },
    ]


def test_get_feature_states_for_identity__transient_identifier__empty_segment__return_expected(
    admin_client: APIClient,
    sdk_client: APIClient,
    default_feature_value: str,
    identity_identifier: str,
    feature: int,
    environment: int,
    identity: int,
    project: id,
) -> None:
    # Given
    # a %0 segment that matches no identity
    response = admin_client.post(
        reverse("api-v1:projects:project-segments-list", args=[project]),
        data=json.dumps(
            {
                "name": "empty-segment",
                "project": project,
                "rules": [
                    {
                        "type": "ALL",
                        "rules": [
                            {
                                "type": "ANY",
                                "rules": [],
                                "conditions": [
                                    {
                                        "operator": "PERCENTAGE_SPLIT",
                                        "value": 0,
                                    }
                                ],
                            }
                        ],
                        "conditions": [],
                    }
                ],
            }
        ),
        content_type="application/json",
    )
    segment_id = response.json()["id"]

    # and a segment override for the %0 segment
    response = admin_client.post(
        reverse("api-v1:features:feature-segment-list"),
        data=json.dumps(
            {
                "feature": feature,
                "segment": segment_id,
                "environment": environment,
            }
        ),
        content_type="application/json",
    )
    feature_segment_id = response.json()["id"]

    admin_client.post(
        reverse("api-v1:features:featurestates-list"),
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {
                    "type": "unicode",
                    "string_value": "segment override",
                },
                "feature": feature,
                "environment": environment,
                "feature_segment": feature_segment_id,
            }
        ),
        content_type="application/json",
    )

    url = reverse("api-v1:sdk-identities")

    # When
    # flags are requested for a transient identifier
    response = sdk_client.post(
        url,
        data=json.dumps(
            {
                "identifier": "",
                "traits": [
                    {
                        "trait_key": "transient",
                        "trait_value": "trait value",
                    },
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert (
        flag_data := next(
            (
                flag
                for flag in response_json["flags"]
                if flag["feature"]["id"] == feature
            ),
            None,
        )
    )
    # flag is not being overridden by the segment
    assert flag_data["enabled"] is False
    assert flag_data["feature_state_value"] == default_feature_value
