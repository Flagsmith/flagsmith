"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Callable
from typing import Any

import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.tasks import enable_v2_versioning


@pytest.fixture(params=["feature_versioning_v1", "feature_versioning_v2"], autouse=True)
def versioned_environment(
    request: pytest.FixtureRequest,
    environment: int,
) -> Environment:
    if request.param == "feature_versioning_v2":
        enable_v2_versioning(environment_id=environment)
    return Environment.objects.get(id=environment)  # type: ignore[no-any-return]


@pytest.fixture()
def segment_2(
    admin_client: APIClient,
    project: int,
) -> int:
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        {
            "name": "Test Segment 2",
            "project": project,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )
    return int(response.json()["id"])


def test_update_flag__environment_default_enabled__toggles_flag(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    feature_name: str,
    versioned_environment: Environment,
) -> None:
    # Given
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is False

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"name": feature_name},
            "environment_default": {"enabled": True},
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is True


def test_update_flag__environment_default_value__updates_value(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "integer", "value": "1000"},
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is True
    assert environment_default.get_feature_state_value() == 1000


@pytest.mark.parametrize(
    "update",
    [
        pytest.param({"value": {"type": "string", "value": "control"}}, id="enabled"),
        pytest.param({"enabled": True}, id="value"),
        pytest.param({}, id="enabled-and-value"),
    ],
)
def test_update_flag__environment_default_attribute_omitted__left_unchanged(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
    update: dict[str, object],
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "control"},
            },
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": update,
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is True
    assert environment_default.get_feature_state_value() == "control"


def test_update_flag__segment_overrides__creates_overrides(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": False,
                "value": {"type": "string", "value": "standard"},
            },
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "priority": 1,
                    "enabled": True,
                    "value": {"type": "string", "value": "enterprise"},
                },
                {
                    "segment_id": segment_2,
                    "priority": 2,
                    "enabled": True,
                    "value": {"type": "string", "value": "premium"},
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
    environment_default = live_feature_states.get(feature_segment=None)
    assert environment_default.enabled is False
    assert environment_default.get_feature_state_value() == "standard"
    enterprise_override = live_feature_states.get(feature_segment__segment_id=segment)
    assert enterprise_override.enabled is True
    assert enterprise_override.get_feature_state_value() == "enterprise"
    premium_override = live_feature_states.get(feature_segment__segment_id=segment_2)
    assert premium_override.enabled is True
    assert premium_override.get_feature_state_value() == "premium"


def test_update_flag__environment_default_variants__creates_variants(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default_gateway"},
                "variants": [
                    {
                        "key": "new_gateway_a",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "sharp_payments"},
                    },
                    {
                        "key": "new_gateway_b",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "e_z_pay"},
                    },
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert dict(
        MultivariateFeatureOption.objects.filter(feature_id=feature).values_list(
            "key", "string_value"
        )
    ) == {"new_gateway_a": "sharp_payments", "new_gateway_b": "e_z_pay"}
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"new_gateway_a": 10, "new_gateway_b": 10}


def test_update_flag__segment_override_variants__reweights_for_segment_only(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default_gateway"},
                "variants": [
                    {
                        "key": "new_gateway_a",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "sharp_payments"},
                    },
                    {
                        "key": "new_gateway_b",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "e_z_pay"},
                    },
                ],
            },
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "enabled": True,
                    "value": {"type": "string", "value": "enterprise_gateway"},
                    "variants": [
                        {"key": "new_gateway_a", "weight": 0.25},
                        {"key": "new_gateway_b", "weight": 0.25},
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
    override = live_feature_states.get(feature_segment__segment_id=segment)
    assert dict(
        override.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"new_gateway_a": 25, "new_gateway_b": 25}
    environment_default = live_feature_states.get(feature_segment=None)
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"new_gateway_a": 10, "new_gateway_b": 10}


def test_update_flag__segment_override_variant_omitted__keeps_weight_for_segment(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default"},
                "variants": [
                    {
                        "key": "variant_a",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "a"},
                    },
                    {
                        "key": "variant_b",
                        "weight": 0.2,
                        "value": {"type": "string", "value": "b"},
                    },
                ],
            },
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "enabled": True,
                    "value": {"type": "string", "value": "override"},
                    "variants": [
                        {"key": "variant_a", "weight": 0.3},
                    ],
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    override = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    ).get(feature_segment__segment_id=segment)
    assert dict(
        override.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_a": 30, "variant_b": 20}


def test_update_flag__environment_default_variant_omitted__deletes_variant(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "enabled": True,
                "value": {"type": "string", "value": "default"},
                "variants": [
                    {
                        "key": "variant_kept",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "kept"},
                    },
                    {
                        "key": "variant_deleted",
                        "weight": 0.2,
                        "value": {"type": "string", "value": "deleted"},
                    },
                ],
            },
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "enabled": True,
                    "value": {"type": "string", "value": "override"},
                    "variants": [
                        {"key": "variant_kept", "weight": 0.3},
                        {"key": "variant_deleted", "weight": 0.4},
                    ],
                },
            ],
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "variants": [
                    {"key": "variant_kept", "weight": 0.5},
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    environment_default = live_feature_states.get(feature_segment=None)
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_kept": 50}
    override = live_feature_states.get(feature_segment__segment_id=segment)
    assert dict(
        override.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_kept": 30}


def test_update_flag__segment_override_delete__removes_override(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "enabled": True,
                    "value": {"type": "string", "value": "override"},
                },
            ],
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {"segment_id": segment, "delete": True},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .filter(feature_segment__segment_id=segment)
        .exists()
    )


def test_update_flag__segment_override_delete_with_other_attributes__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {"segment_id": segment, "delete": True, "enabled": True},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "delete" in str(response.json())


@pytest.mark.parametrize(
    "update",
    [
        pytest.param(
            lambda segment: {
                "environment_default": {
                    "variants": [
                        {"key": "variant_a", "weight": 0.6},
                        {"key": "variant_b", "weight": 0.5},
                    ],
                },
            },
            id="environment-default",
        ),
        pytest.param(
            lambda segment: {
                "segment_overrides": [
                    {
                        "segment_id": segment,
                        "variants": [
                            {"key": "variant_a", "weight": 0.6},
                            {"key": "variant_b", "weight": 0.5},
                        ],
                    },
                ],
            },
            id="segment-override",
        ),
    ],
)
def test_update_flag__variant_weights_exceed_one__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
    update: Callable[[int], dict[str, Any]],
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "variants": [
                    {
                        "key": "variant_a",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "a"},
                    },
                    {
                        "key": "variant_b",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "b"},
                    },
                ],
            },
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            **update(segment),
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "variants" in str(response.json())
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_a": 10, "variant_b": 10}


@pytest.mark.parametrize(
    "variant",
    [
        pytest.param(
            {
                "key": "variant_a",
                "weight": 0.5,
                "value": {"type": "string", "value": "changed"},
            },
            id="value-provided",
        ),
        pytest.param(
            {"key": "unknown_variant", "weight": 0.5},
            id="unknown-key",
        ),
    ],
)
def test_update_flag__segment_override_variant_not_reweighting__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    variant: dict[str, Any],
) -> None:
    # Given
    setup_response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {
                "variants": [
                    {
                        "key": "variant_a",
                        "weight": 0.1,
                        "value": {"type": "string", "value": "a"},
                    },
                ],
            },
        },
        format="json",
    )
    assert setup_response.status_code == 204

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {
                    "segment_id": segment,
                    "variants": [variant],
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "variants" in str(response.json())


def test_update_flag__unknown_feature__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"name": "unknown_feature"},
            "environment_default": {"enabled": True},
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "feature" in str(response.json()).lower()


def test_update_flag__unknown_segment__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "segment_overrides": [
                {"segment_id": 999999, "enabled": True},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert "segment" in str(response.json()).lower()


def test_update_flag__change_requests_enabled__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
) -> None:
    # Given
    versioned_environment.minimum_change_request_approvals = 0
    versioned_environment.save()

    # When
    response = admin_client.post(
        f"/api/experiments/environments/{environment_api_key}/update-flag/",
        {
            "feature": {"id": feature},
            "environment_default": {"enabled": True},
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is False
