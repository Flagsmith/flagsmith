"""https://docs.flagsmith.com/managing-flags/updating-flags"""

import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from features.future.types import UpdateFlagRequest
from features.models import FeatureState
from features.versioning.tasks import enable_v2_versioning
from tests.integration.helpers import create_mv_option_with_api


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


@pytest.fixture()
def mv_feature_variants(
    admin_client: APIClient,
    project: int,
    mv_feature: int,
) -> None:
    for key, value, default_percentage_allocation in [
        ("variant_a", "a", 10),
        ("variant_b", "b", 20),
    ]:
        create_mv_option_with_api(
            admin_client,
            project,
            mv_feature,
            default_percentage_allocation,
            value,
            key=key,
        )


def test_update_flag__patch_environment_default_enabled__toggles_flag(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
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
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [],
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is True


def test_update_flag__patch_environment_default_value__updates_value(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"environment_default": {"value": {"type": "integer", "value": "1000"}}}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "integer", "value": "1000"},
            "variants": [],
        },
        "segment_overrides": [],
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.get_feature_state_value() == 1000


@pytest.mark.usefixtures("mv_feature_variants")
def test_update_flag__patch_environment_default_variants__reweights_variants(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    mv_feature: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"key": "variant_a", "weight": 25},
                        {"key": "variant_b", "weight": 25.5},
                    ],
                },
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [
                {"key": "variant_a", "weight": 25},
                {"key": "variant_b", "weight": 25.5},
            ],
        },
        "segment_overrides": [],
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_a": 25, "variant_b": 25.5}


def test_update_flag__patch_segment_override_enabled__creates_override(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "enabled": True}]}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
        ],
    }
    override = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    ).get(feature_segment__segment_id=segment)
    assert override.feature_segment is not None
    assert override.feature_segment.priority == 0
    assert override.enabled is True
    assert override.get_feature_state_value() == default_feature_value


def test_update_flag__patch_segment_override_value__overrides_value(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "value": {"type": "string", "value": "enterprise"},
                    },
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": False,
                "value": {"type": "string", "value": "enterprise"},
                "variants": [],
            },
        ],
    }
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert (
        live_feature_states.get(
            feature_segment__segment_id=segment
        ).get_feature_state_value()
        == "enterprise"
    )
    assert (
        live_feature_states.get(feature_segment=None).get_feature_state_value()
        == default_feature_value
    )


def test_update_flag__patch_segment_override_without_value__inherits_environment_default_value(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"environment_default": {"value": {"type": "string", "value": "control"}}}
        ),
        format="json",
    )
    assert setup_response.status_code == 200

    # When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "enabled": True}]}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": "control"},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "value": "control"},
                "variants": [],
            },
        ],
    }
    override = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    ).get(feature_segment__segment_id=segment)
    assert override.get_feature_state_value() == "control"


def test_update_flag__patch_segment_overrides_without_priority__sets_priority_from_position(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment}, "enabled": True},
                    {"segment": {"id": segment_2}, "enabled": True},
                ],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    assert [
        (override["segment"]["id"], override["priority"])
        for override in setup_response.json()["segment_overrides"]
    ] == [(segment, 0), (segment_2, 1)]  # Priority is inferred when creating overrides

    # When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment_2}, "enabled": False},  # No priority
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
            {
                "segment": {"id": segment_2},
                "priority": 1,  # Priority is preserved from previous state
                "enabled": False,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
        ],
    }
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .values_list("feature_segment__segment_id", "feature_segment__priority")
    ) == {segment: 0, segment_2: 1}


def test_update_flag__patch_segment_override_priority__writes_priority_as_given(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment}, "priority": 10, "enabled": True},
                    {"segment": {"id": segment_2}, "enabled": True},
                ],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    assert [
        (override["segment"]["id"], override["priority"])
        for override in setup_response.json()["segment_overrides"]
    ] == [(segment_2, 1), (segment, 10)]

    # When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "priority": 1}]}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 1,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
            {
                "segment": {"id": segment_2},
                "priority": 1,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
        ],
    }
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .values_list("feature_segment__segment_id", "feature_segment__priority")
    ) == {segment: 1, segment_2: 1}


@pytest.mark.usefixtures("mv_feature_variants")
def test_update_flag__patch_segment_override_variants__reweights_for_segment_only(
    admin_client: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    mv_feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "variants": [
                            {"key": "variant_a", "weight": 25},
                            {"key": "variant_b", "weight": 25.5},
                        ],
                    },
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [
                {"key": "variant_a", "weight": 10},
                {"key": "variant_b", "weight": 20},
            ],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": False,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [
                    {"key": "variant_a", "weight": 25},
                    {"key": "variant_b", "weight": 25.5},
                ],
            },
        ],
    }
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
    )
    assert dict(
        live_feature_states.get(
            feature_segment__segment_id=segment
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_a": 25, "variant_b": 25.5}
    assert dict(
        live_feature_states.get(
            feature_segment=None
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option__key", "percentage_allocation"
        )
    ) == {"variant_a": 10, "variant_b": 20}


def test_update_flag__put_environment_default__replaces_environment_default(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "control"},
                },
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200

    # When
    response = admin_client.put(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": True,
            "value": None,
            "variants": [],
        },
        "segment_overrides": [],
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is True
    assert environment_default.get_feature_state_value() is None


def test_update_flag__put_segment_overrides__replaces_segment_overrides(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "control"},
                },
                "segment_overrides": [
                    {"segment": {"id": segment}, "enabled": True},
                    {"segment": {"id": segment_2}, "enabled": True},
                ],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200

    # When
    response = admin_client.put(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "priority": 10,
                        "value": {"type": "string", "value": "enterprise"},
                    },
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "value": "control"},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 10,
                "enabled": False,
                "value": {"type": "string", "value": "enterprise"},
                "variants": [],
            },
        ],
    }
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert dict(
        live_feature_states.exclude(feature_segment=None).values_list(
            "feature_segment__segment_id", "feature_segment__priority"
        )
    ) == {segment: 10}
    assert (
        live_feature_states.get(feature_segment=None).get_feature_state_value()
        == "control"
    )


def test_update_flag__put_environment_default_and_segment_overrides__replaces_both(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "control"},
                },
                "segment_overrides": [
                    {"segment": {"id": segment_2}, "enabled": True},
                ],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200

    # When
    response = admin_client.put(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": False,
                    "value": {"type": "integer", "value": "42"},
                },
                "segment_overrides": [
                    {"segment": {"id": segment}, "priority": 5, "enabled": True},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "integer", "value": "42"},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 5,
                "enabled": True,
                # Inherited from the environment default written in the same request
                "value": {"type": "integer", "value": "42"},
                "variants": [],
            },
        ],
    }
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert live_feature_states.get(feature_segment=None).get_feature_state_value() == 42
    assert dict(
        live_feature_states.exclude(feature_segment=None).values_list(
            "feature_segment__segment_id", "feature_segment__priority"
        )
    ) == {segment: 5}
    assert (
        live_feature_states.get(
            feature_segment__segment_id=segment
        ).get_feature_state_value()
        == 42
    )
