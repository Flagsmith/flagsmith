"""https://docs.flagsmith.com/integrating-with-flagsmith/flagsmith-api-overview/admin-api/updating-flags"""

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, Literal, TypeAlias

import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from features.feature_types import STANDARD
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.tasks import enable_v2_versioning
from tests.integration.helpers import create_mv_option_with_api

FeatureUpdatePayload: TypeAlias = dict[str, Any]
VariantIdentifier: TypeAlias = dict[str, Any]
UpdateFlagEndpointOption = Literal["update-flag-v1", "update-flag-v2"]


@pytest.fixture(params=["feature_versioning_v1", "feature_versioning_v2"], autouse=True)
def versioned_environment(
    request: pytest.FixtureRequest,
    environment: int,
) -> Environment:
    if request.param == "feature_versioning_v2":
        enable_v2_versioning(environment_id=environment)
    return Environment.objects.get(id=environment)  # type: ignore[no-any-return]


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature: {
                "feature": {"id": feature},
                "value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "key": "one-half",
                        "percentage_allocation": 50,
                        "value": {"type": "string", "value": "half"},
                    },
                    {
                        "percentage_allocation": 10,
                        "value": {"type": "string", "value": "bit more"},
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature: {
                "feature": {"id": feature},
                "environment_default": {
                    "value": {"type": "string", "value": "control"},
                    "multivariate_feature_state_values": [
                        {
                            "key": "one-half",
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "half"},
                        },
                        {
                            "percentage_allocation": 10,
                            "value": {"type": "string", "value": "bit more"},
                        },
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__environment_defaults__adds_multivariate_options(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int], FeatureUpdatePayload],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature),
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
            feature_segment=None,
        )
        .get()
        .multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value", "percentage_allocation"
        )
    ) == {"half": 50, "bit more": 10}
    assert dict(
        MultivariateFeatureOption.objects.filter(feature_id=feature).values_list(
            "string_value", "key"
        )
    ) == {"half": "one-half", "bit more": None}


@pytest.mark.parametrize(
    "variant_identifier",
    [
        pytest.param(
            lambda option_id, option_key: {"multivariate_feature_option": option_id},
            id="by_id",
        ),
        pytest.param(lambda option_id, option_key: {"key": option_key}, id="by_key"),
    ],
)
@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature, identifier: {
                "feature": {"id": feature},
                "multivariate_feature_state_values": [
                    {
                        **identifier,
                        "percentage_allocation": 25,
                        "value": {"type": "string", "value": "halfer"},
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature, identifier: {
                "feature": {"id": feature},
                "environment_default": {
                    "multivariate_feature_state_values": [
                        {
                            **identifier,
                            "percentage_allocation": 25,
                            "value": {"type": "string", "value": "halfer"},
                        },
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__environment_defaults__updates_multivariate_options(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    mv_option_50_percent: int,
    mv_option_key: str,
    versioned_environment: Environment,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int, VariantIdentifier], FeatureUpdatePayload],
    variant_identifier: Callable[[int, str], VariantIdentifier],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature, variant_identifier(mv_option_50_percent, mv_option_key)),
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
            feature_segment=None,
        )
        .get()
        .multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value", "percentage_allocation"
        )
    ) == {"halfer": 25}
    assert (
        MultivariateFeatureOption.objects.get(
            id=mv_option_50_percent
        ).default_percentage_allocation
        == 25
    )


@pytest.mark.parametrize(
    "variant_identifier",
    [
        pytest.param(
            lambda option_id, option_key: {"multivariate_feature_option": option_id},
            id="by_id",
        ),
        pytest.param(lambda option_id, option_key: {"key": option_key}, id="by_key"),
    ],
)
@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature, segment, identifier: {
                "feature": {"id": feature},
                "segment": {"id": segment},
                "multivariate_feature_state_values": [
                    {**identifier, "percentage_allocation": 80},
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature, segment, identifier: {
                "feature": {"id": feature},
                "segment_overrides": [
                    {
                        "segment_id": segment,
                        "multivariate_feature_state_values": [
                            {**identifier, "percentage_allocation": 80},
                        ],
                    },
                ],
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__segment_override__updates_multivariate_options(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    mv_option_value: str,
    mv_option_50_percent: int,
    mv_option_key: str,
    segment: int,
    versioned_environment: Environment,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int, int, VariantIdentifier], FeatureUpdatePayload],
    variant_identifier: Callable[[int, str], VariantIdentifier],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(
            feature, segment, variant_identifier(mv_option_50_percent, mv_option_key)
        ),
        format="json",
    )

    # Then
    assert response.status_code == 204
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert dict(
        live_feature_states.get(
            feature_segment__segment_id=segment
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value", "percentage_allocation"
        )
    ) == {mv_option_value: 80}
    assert dict(
        live_feature_states.get(
            feature_segment=None
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value", "percentage_allocation"
        )
    ) == {mv_option_value: 50}


@pytest.mark.parametrize(
    "variant_identifier",
    [
        pytest.param(
            lambda option_id, option_key: {"multivariate_feature_option": option_id},
            id="by_id",
        ),
        pytest.param(lambda option_id, option_key: {"key": option_key}, id="by_key"),
    ],
)
@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature, identifier: {
                "feature": {"id": feature},
                "multivariate_feature_state_values": [
                    {**identifier, "percentage_allocation": 50},
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature, identifier: {
                "feature": {"id": feature},
                "environment_default": {
                    "multivariate_feature_state_values": [
                        {**identifier, "percentage_allocation": 50},
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__environment_defaults__deletes_multivariate_options(
    admin_client: APIClient,
    environment_api_key: str,
    project: int,
    feature: int,
    mv_option_50_percent: int,
    mv_option_key: str,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int, VariantIdentifier], FeatureUpdatePayload],
    variant_identifier: Callable[[int, str], VariantIdentifier],
) -> None:
    # Given
    deleted_option = create_mv_option_with_api(
        admin_client, project, feature, 40, "other_mv_value"
    )

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature, variant_identifier(mv_option_50_percent, mv_option_key)),
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert not MultivariateFeatureOption.objects.filter(id=deleted_option).exists()
    assert MultivariateFeatureOption.objects.filter(id=mv_option_50_percent).exists()


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature: {
                "feature": {"id": feature},
                "multivariate_feature_state_values": [
                    {
                        "percentage_allocation": 60,
                        "value": {"type": "string", "value": "more"},
                    },
                    {
                        "percentage_allocation": 50,
                        "value": {"type": "string", "value": "less"},
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature: {
                "feature": {"id": feature},
                "environment_default": {
                    "multivariate_feature_state_values": [
                        {
                            "percentage_allocation": 60,
                            "value": {"type": "string", "value": "more"},
                        },
                        {
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "less"},
                        },
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__multivariate_percentage_allocation_exceeds_100__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int], FeatureUpdatePayload],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "multivariate_feature_state_values" in response.json()
    assert not MultivariateFeatureOption.objects.filter(feature_id=feature).exists()


@pytest.mark.parametrize(
    ["endpoint", "payload", "expected_errors"],
    [
        test_case
        for scenario in [
            SimpleNamespace(
                id="add-without-value",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {"percentage_allocation": 50}
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {
                                "non_field_errors": [
                                    "A new multivariate option requires a 'value'."
                                ]
                            }
                        ]
                    },
                    {  # Option B
                        "environment_default": {
                            "multivariate_feature_state_values": [
                                {
                                    "non_field_errors": [
                                        "A new multivariate option requires a 'value'."
                                    ]
                                }
                            ]
                        }
                    },
                ],
            ),
            SimpleNamespace(
                id="add-without-allocation",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {"value": {"type": "string", "value": "variant"}},
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {"percentage_allocation": ["This field is required."]}
                        ]
                    },
                    {  # Option B
                        "environment_default": {
                            "multivariate_feature_state_values": [
                                {"percentage_allocation": ["This field is required."]}
                            ]
                        }
                    },
                ],
            ),
            SimpleNamespace(
                id="unknown",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": 999999,
                            "percentage_allocation": 50,
                        },
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options [999999] do not belong to the feature"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="both-id-and-key",
                payload=lambda multivariate_option_id, multivariate_option_key, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "key": multivariate_option_key,
                            "percentage_allocation": 50,
                        },
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {
                                "non_field_errors": [
                                    "Provide either 'multivariate_feature_option' or 'key', not both"
                                ]
                            }
                        ]
                    },
                    {  # Option B
                        "environment_default": {
                            "multivariate_feature_state_values": [
                                {
                                    "non_field_errors": [
                                        "Provide either 'multivariate_feature_option' or 'key', not both"
                                    ]
                                }
                            ]
                        }
                    },
                ],
            ),
            SimpleNamespace(
                id="new-key-without-value",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {"key": "brand-new", "percentage_allocation": 50},
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "A new multivariate option requires a 'value'."
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="reserved-key",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {
                            "key": "control",
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "variant"},
                        },
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {"key": ['"control" is a reserved variant key.']}
                        ]
                    },
                    {  # Option B
                        "environment_default": {
                            "multivariate_feature_state_values": [
                                {"key": ['"control" is a reserved variant key.']}
                            ]
                        }
                    },
                ],
            ),
            SimpleNamespace(
                id="invalid-slug-key",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {
                            "key": "not a key!",
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "variant"},
                        },
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {
                                "key": [
                                    'Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'
                                ]
                            }
                        ]
                    },
                    {  # Option B
                        "environment_default": {
                            "multivariate_feature_state_values": [
                                {
                                    "key": [
                                        'Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'
                                    ]
                                }
                            ]
                        }
                    },
                ],
            ),
            SimpleNamespace(
                id="duplicate-key",
                payload=lambda multivariate_option_key, **_: {
                    "multivariate_feature_state_values": [
                        {"key": multivariate_option_key, "percentage_allocation": 60},
                        {"key": multivariate_option_key, "percentage_allocation": 40},
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options must be unique"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="duplicate-mixed-id-and-key",
                payload=lambda multivariate_option_id, multivariate_option_key, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 60,
                        },
                        {"key": multivariate_option_key, "percentage_allocation": 40},
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options must be unique"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="duplicate",
                payload=lambda multivariate_option_id, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 60,
                        },
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 40,
                        },
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options must be unique"
                        ]
                    },
                ],
            ),
        ]
        for test_case in [
            pytest.param(
                "update-flag-v1",
                scenario.payload,
                scenario.expected_errors,
                id=f"{scenario.id}-option_a",
            ),
            pytest.param(
                "update-flag-v2",
                lambda scenario=scenario, **kw: {
                    "environment_default": scenario.payload(**kw),
                },
                scenario.expected_errors,
                id=f"{scenario.id}-option_b",
            ),
        ]
    ],
)
def test_update_flag__invalid_environment_multivariate_options__responds_400(
    admin_client: APIClient,
    endpoint: UpdateFlagEndpointOption,
    environment_api_key: str,
    expected_errors: list[Any],
    feature: int,
    mv_option_50_percent: int,
    mv_option_key: str,
    payload: Callable[..., FeatureUpdatePayload],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        data={
            "feature": {"id": feature},
            **payload(
                multivariate_option_id=mv_option_50_percent,
                multivariate_option_key=mv_option_key,
            ),
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() in expected_errors


@pytest.mark.parametrize(
    ["endpoint", "payload", "expected_errors"],
    [
        test_case
        for scenario in [
            SimpleNamespace(
                id="without-identifier",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "variant"},
                        },
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            "Segment overrides require a variant 'id' or 'key'."
                        ]
                    },
                    {  # Option B
                        "segment_overrides": [
                            {
                                "multivariate_feature_state_values": [
                                    {
                                        "non_field_errors": [
                                            "Segment overrides require a variant 'id' or 'key'."
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="both-id-and-key",
                payload=lambda multivariate_option_id, multivariate_option_key, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "key": multivariate_option_key,
                            "percentage_allocation": 50,
                        },
                    ],
                },
                expected_errors=[
                    {  # Option A
                        "multivariate_feature_state_values": [
                            {
                                "non_field_errors": [
                                    "Provide either 'multivariate_feature_option' or 'key', not both"
                                ]
                            }
                        ]
                    },
                    {  # Option B
                        "segment_overrides": [
                            {
                                "multivariate_feature_state_values": [
                                    {
                                        "non_field_errors": [
                                            "Provide either 'multivariate_feature_option' or 'key', not both"
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="unknown-key",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {"key": "ghost", "percentage_allocation": 50},
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate keys ['ghost'] do not belong to the feature"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="unknown-id",
                payload=lambda **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": 999999,
                            "percentage_allocation": 50,
                        },
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options [999999] do not belong to the feature"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="duplicate",
                payload=lambda multivariate_option_id, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 60,
                        },
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 40,
                        },
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options must be unique"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="duplicate-key",
                payload=lambda multivariate_option_key, **_: {
                    "multivariate_feature_state_values": [
                        {"key": multivariate_option_key, "percentage_allocation": 60},
                        {"key": multivariate_option_key, "percentage_allocation": 40},
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Multivariate options must be unique"
                        ]
                    },
                ],
            ),
            SimpleNamespace(
                id="with-value",
                payload=lambda multivariate_option_id, **_: {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": multivariate_option_id,
                            "percentage_allocation": 50,
                            "value": {"type": "string", "value": "variant"},
                        },
                    ],
                },
                expected_errors=[
                    {
                        "multivariate_feature_state_values": [
                            "Segment overrides can only re-weight existing variants.",
                        ],
                    },
                ],
            ),
        ]
        for test_case in [
            pytest.param(
                "update-flag-v1",
                lambda segment_id, scenario=scenario, **kw: {
                    "segment": {"id": segment_id},
                    **scenario.payload(**kw),
                },
                scenario.expected_errors,
                id=f"{scenario.id}-option_a",
            ),
            pytest.param(
                "update-flag-v2",
                lambda segment_id, scenario=scenario, **kw: {
                    "segment_overrides": [
                        {
                            "segment_id": segment_id,
                            **scenario.payload(**kw),
                        },
                    ],
                },
                scenario.expected_errors,
                id=f"{scenario.id}-option_b",
            ),
        ]
    ],
)
def test_update_flag__invalid_segment_multivariate_options__responds_400(
    admin_client: APIClient,
    endpoint: UpdateFlagEndpointOption,
    environment_api_key: str,
    expected_errors: list[Any],
    feature: int,
    mv_option_50_percent: int,
    mv_option_key: str,
    payload: Callable[..., FeatureUpdatePayload],
    segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        data={
            "feature": {"id": feature},
            **payload(
                multivariate_option_id=mv_option_50_percent,
                multivariate_option_key=mv_option_key,
                segment_id=segment,
            ),
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() in expected_errors


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature: {
                "feature": {"id": feature},
                "multivariate_feature_state_values": [],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature: {
                "feature": {"id": feature},
                "environment_default": {"multivariate_feature_state_values": []},
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__empty_multivariate_list__deletes_all_options(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    mv_option_50_percent: int,
    versioned_environment: Environment,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int], FeatureUpdatePayload],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature),
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert not MultivariateFeatureOption.objects.filter(feature_id=feature).exists()
    assert Feature.objects.get(id=feature).type == STANDARD
    assert not (
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
            feature_segment=None,
        )
        .get()
        .multivariate_feature_state_values.exists()
    )


@pytest.mark.parametrize(
    "endpoint,setup_payload,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature: {
                "feature": {"id": feature},
                "enabled": True,
                "value": {"type": "string", "value": "control"},
            },
            lambda feature, segment, option: {
                "feature": {"id": feature},
                "segment": {"id": segment},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": option,
                        "percentage_allocation": 80,
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature: {
                "feature": {"id": feature},
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "control"},
                },
            },
            lambda feature, segment, option: {
                "feature": {"id": feature},
                "segment_overrides": [
                    {
                        "segment_id": segment,
                        "multivariate_feature_state_values": [
                            {
                                "multivariate_feature_option": option,
                                "percentage_allocation": 80,
                            },
                        ],
                    },
                ],
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__new_segment_override_without_enabled_and_value__inherits_environment_default(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    mv_option_50_percent: int,
    segment: int,
    versioned_environment: Environment,
    endpoint: UpdateFlagEndpointOption,
    setup_payload: Callable[[int], FeatureUpdatePayload],
    payload: Callable[[int, int, int], FeatureUpdatePayload],
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        setup_payload(feature),
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature, segment, mv_option_50_percent),
        format="json",
    )

    # Then
    assert response.status_code == 204
    override_feature_state = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    ).get(feature_segment__segment_id=segment)
    assert override_feature_state.enabled is True
    assert override_feature_state.get_feature_state_value() == "control"


@pytest.mark.parametrize(
    "variant_identifier",
    [
        pytest.param(
            lambda option_id, option_key: {"multivariate_feature_option": option_id},
            id="by_id",
        ),
        pytest.param(lambda option_id, option_key: {"key": option_key}, id="by_key"),
    ],
)
def test_update_flag_option_b__segment_override_reweights_option_deleted_from_environment__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    mv_option_50_percent: int,
    mv_option_key: str,
    segment: int,
    variant_identifier: Callable[[int, str], VariantIdentifier],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag-v2/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "multivariate_feature_state_values": [
                    {
                        "percentage_allocation": 30,
                        "value": {"type": "string", "value": "replacement"},
                    },
                ],
            },
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "multivariate_feature_state_values": [
                        {
                            **variant_identifier(mv_option_50_percent, mv_option_key),
                            "percentage_allocation": 80,
                        },
                    ],
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "multivariate_feature_state_values": [
            "Segment overrides can only re-weight existing variants."
        ]
    }


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda option: {
                "feature": {"name": "unknown_feature"},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": option,
                        "percentage_allocation": 50,
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda option: {
                "feature": {"name": "unknown_feature"},
                "environment_default": {
                    "multivariate_feature_state_values": [
                        {
                            "multivariate_feature_option": option,
                            "percentage_allocation": 50,
                        },
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__unknown_feature_with_multivariate_options__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    mv_option_50_percent: int,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int], FeatureUpdatePayload],
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(mv_option_50_percent),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "not found in project" in str(response.json())


def test_update_flag_option_b__keyed_variants_in_single_request__configures_environment_and_overrides_segment(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag-v2/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "key": "gold",
                        "percentage_allocation": 30,
                        "value": {"type": "string", "value": "#ffd700"},
                    },
                    {
                        "key": "silver",
                        "percentage_allocation": 10,
                        "value": {"type": "string", "value": "#c0c0c0"},
                    },
                ],
            },
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "multivariate_feature_state_values": [
                        {"key": "gold", "percentage_allocation": 100},
                        {"key": "silver", "percentage_allocation": 0},
                    ],
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert dict(
        live_feature_states.get(
            feature_segment=None
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"gold": 30, "silver": 10}
    assert dict(
        live_feature_states.get(
            feature_segment__segment_id=segment
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"gold": 100, "silver": 0}


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        pytest.param(
            "update-flag-v1",
            lambda feature: {
                "feature": {"id": feature},
                "multivariate_feature_state_values": [
                    {
                        "key": "gold",
                        "percentage_allocation": 30,
                        "value": {"type": "string", "value": "#ffd700"},
                    },
                ],
            },
            id="option_a",
        ),
        pytest.param(
            "update-flag-v2",
            lambda feature: {
                "feature": {"id": feature},
                "environment_default": {
                    "multivariate_feature_state_values": [
                        {
                            "key": "gold",
                            "percentage_allocation": 30,
                            "value": {"type": "string", "value": "#ffd700"},
                        },
                    ],
                },
            },
            id="option_b",
        ),
    ],
)
def test_update_flag__repeated_keyed_multivariate_payload__preserves_variant_identities(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    endpoint: UpdateFlagEndpointOption,
    payload: Callable[[int], FeatureUpdatePayload],
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature),
        format="json",
    )
    assert setup_response.status_code == 204
    option_ids = set(
        MultivariateFeatureOption.objects.filter(feature_id=feature).values_list(
            "id", flat=True
        )
    )

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/{endpoint}/",
        payload(feature),
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert (
        set(
            MultivariateFeatureOption.objects.filter(feature_id=feature).values_list(
                "id", flat=True
            )
        )
        == option_ids
    )
