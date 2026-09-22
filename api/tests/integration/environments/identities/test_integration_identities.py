import hashlib
import json
from typing import Any, Generator
from unittest import mock

import pytest
from django.urls import reverse
from pytest_lazy_fixtures import lf as lazy_fixture
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


def _set_mv_allocations(
    admin_client: APIClient,
    environment_api_key: str,
    feature_state_id: int,
    allocation_by_mv_option_id: dict[int, float],
) -> None:
    """Reallocate a multivariate feature state's variants, through the API."""
    feature_state_detail_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state_id],
    )
    feature_state_data = admin_client.get(feature_state_detail_url).json()
    for mv_value in feature_state_data["multivariate_feature_state_values"]:
        mv_value["percentage_allocation"] = allocation_by_mv_option_id[
            mv_value["multivariate_feature_option"]
        ]
    update_response = admin_client.put(
        feature_state_detail_url,
        data=json.dumps(feature_state_data),
        content_type="application/json",
    )
    assert update_response.status_code == status.HTTP_200_OK


# Which variant an identity hashes into is not something an API test can pin
# down, so each case allocates a single variant the whole range instead.
@pytest.mark.parametrize(
    [
        "variant_1_allocation",
        "variant_2_allocation",
        "expected_value",
        "expected_variant",
    ],
    (
        pytest.param(100, 0, variant_1_value, "variant-1", id="all_variant_1"),
        pytest.param(0, 100, variant_2_value, "variant-2", id="all_variant_2"),
        pytest.param(0, 0, control_value, "control", id="unallocated_falls_through"),
    ),
)
def test_get_feature_states_for_identity__mv_allocation__returns_value_and_variant(  # type: ignore[no-untyped-def]
    variant_1_allocation,
    variant_2_allocation,
    expected_value,
    expected_variant,
    sdk_client,
    admin_client,
    project,
    environment_api_key,
    environment,
    identity,
    identity_identifier,
):
    # Given
    # a standard (non-multivariate) feature
    standard_feature_initial_value = "control"
    standard_feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="standard_feature",
        initial_value=standard_feature_initial_value,
    )

    # and a multivariate feature with two keyed variants
    multivariate_feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="multivariate_feature",
        initial_value=control_value,
        feature_type=MULTIVARIATE,
    )
    variant_1_mvfo_id = create_mv_option_with_api(
        admin_client,
        project,
        multivariate_feature_id,
        variant_1_percentage_allocation,
        variant_1_value,
        key="variant-1",
    )
    variant_2_mvfo_id = create_mv_option_with_api(
        admin_client,
        project,
        multivariate_feature_id,
        variant_2_percentage_allocation,
        variant_2_value,
        key="variant-2",
    )

    base_identity_flags_url = reverse("api-v1:sdk-identities")
    identity_flags_url = f"{base_identity_flags_url}?identifier={identity_identifier}"
    flags = sdk_client.get(identity_flags_url).json()["flags"]
    multivariate_feature_state_id = next(
        flag["id"] for flag in flags if flag["feature"]["id"] == multivariate_feature_id
    )

    # When
    # the whole range is allocated to one variant, or to neither
    _set_mv_allocations(
        admin_client,
        environment_api_key,
        multivariate_feature_state_id,
        {
            variant_1_mvfo_id: variant_1_allocation,
            variant_2_mvfo_id: variant_2_allocation,
        },
    )
    response = sdk_client.get(identity_flags_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    flags = response.json()["flags"]
    assert len(flags) == 2
    flags_by_feature_id = {flag["feature"]["id"]: flag for flag in flags}

    # the multivariate flag serves the allocated variant, reporting its key,
    # falling through to the control value when nothing is allocated
    assert (
        flags_by_feature_id[multivariate_feature_id]["feature_state_value"]
        == expected_value
    )
    assert flags_by_feature_id[multivariate_feature_id]["variant"] == expected_variant

    # and the standard flag is unaffected, and has no variant
    assert (
        flags_by_feature_id[standard_feature_id]["feature_state_value"]
        == standard_feature_initial_value
    )
    assert flags_by_feature_id[standard_feature_id]["variant"] is None


def test_get_flags__multivariate_feature__response_excludes_variant(  # type: ignore[no-untyped-def]
    sdk_client,
    admin_client,
    project,
    environment,
):
    # Given - a multivariate feature with a keyed variant
    multivariate_feature_id = create_feature_with_api(
        client=admin_client,
        project_id=project,
        feature_name="multivariate_feature",
        initial_value=control_value,
        feature_type=MULTIVARIATE,
    )
    create_mv_option_with_api(
        admin_client,
        project,
        multivariate_feature_id,
        100,
        variant_1_value,
        key="variant-1",
    )

    # When - the environment flags are fetched (no identity / remote evaluation)
    response = sdk_client.get(reverse("api-v1:flags"))

    # Then - variant and metadata are scoped to the identities endpoint only
    assert response.status_code == status.HTTP_200_OK
    assert all("variant" not in flag for flag in response.json())
    assert all("metadata" not in flag for flag in response.json())


def test_get_feature_states_for_identity__multiple_mv_features__single_mv_query(  # type: ignore[no-untyped-def]
    sdk_client,
    admin_client,
    project,
    environment,
    identity,
    identity_identifier,
    django_assert_num_queries,
):
    # Given / When
    # Then
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

    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity_identifier}"

    with django_assert_num_queries(7) as captured:
        first_identity_response = sdk_client.get(url)
    expected_queries = [
        query
        for query in captured.captured_queries
        if 'FROM "multivariate_multivariatefeaturestatevalue"' in query["sql"]
    ]
    assert len(expected_queries) == 1

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

    with django_assert_num_queries(6) as captured:
        second_identity_response = sdk_client.get(url)
    expected_queries = [
        query
        for query in captured.captured_queries
        if 'FROM "multivariate_multivariatefeaturestatevalue"' in query["sql"]
    ]
    assert len(expected_queries) == 1

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
    return hashlib.sha256(  # type: ignore[return-value]
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
def test_get_feature_states_for_identity__segment_matching_traits__returns_segment_override(
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


def test_get_feature_states_for_identity__transient_trait_existing_identity__returns_expected_traits(
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


def test_get_feature_states_for_identity__transient_identifier_empty_segment__returns_default_value(
    admin_client: APIClient,
    sdk_client: APIClient,
    default_feature_value: str,
    identity_identifier: str,
    feature: int,
    environment: int,
    identity: int,
    project: id,  # type: ignore[valid-type]
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
                                        "property": "$.identity.key",
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
