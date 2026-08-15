"""https://docs.flagsmith.com/managing-flags/updating-flags"""

import pytest
from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
    UPDATE_FEATURE_STATE,
)
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from features.future.types import UpdateFlagRequest
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning
from organisations.models import Organisation
from tests.integration.helpers import create_mv_option_with_api
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser


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
    assert response.status_code == 201
    return int(response.json()["id"])


@pytest.fixture()
def segment_in_other_project(
    admin_client: APIClient,
    organisation: int,
) -> int:
    project_response = admin_client.post(
        "/api/v1/projects/",
        {"name": "Other Project", "organisation": organisation},
        format="json",
    )
    assert project_response.status_code == 201
    other_project = project_response.json()["id"]
    response = admin_client.post(
        f"/api/v1/projects/{other_project}/segments/",
        {
            "name": "Other Segment",
            "project": other_project,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )
    assert response.status_code == 201
    return int(response.json()["id"])


@pytest.fixture()
def mv_feature_variants(
    admin_client: APIClient,
    project: int,
    mv_feature: int,
) -> list[int]:
    return [
        create_mv_option_with_api(
            admin_client,
            project,
            mv_feature,
            default_percentage_allocation,
            value,
        )
        for value, default_percentage_allocation in [("a", 10), ("b", 20)]
    ]


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(UpdateFlagRequest({}), id="no_properties"),
        pytest.param(
            UpdateFlagRequest({"environment_default": {}}),
            id="empty_environment_default",
        ),
        pytest.param(
            UpdateFlagRequest({"segment_overrides": []}), id="empty_segment_overrides"
        ),
    ],
)
def test_update_flag__patch_changing_nothing__writes_nothing(
    admin_client_new: APIClient,
    changes: UpdateFlagRequest,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given
    versions = EnvironmentFeatureVersion.objects.filter(
        environment=versioned_environment, feature_id=feature
    )
    version_count = versions.count()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        changes,
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
        "segment_overrides": [],
    }
    assert versions.count() == version_count
    assert log.events == []


def test_get_flag__user_authorised__returns_flag_state(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {"enabled": True},
                "segment_overrides": [{"segment": {"id": segment}, "priority": 3}],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    log.events.clear()

    # When
    response = admin_client_new.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": True,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 3,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
        ],
    }
    assert log.events == []


def test_get_flag__change_requests_enabled__returns_flag_state(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given
    versioned_environment.minimum_change_request_approvals = 2
    versioned_environment.save()

    # When
    response = admin_client_new.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "environment_default": {
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        "segment_overrides": [],
    }
    assert log.events == []


def test_get_flag__user_not_authorised__responds_404(
    non_admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = non_admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert log.events == []


def test_update_flag__patch_environment_default_enabled__toggles_flag(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
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
    response = admin_client_new.patch(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_environment_default_value__updates_value(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_environment_default_variants__reweights_variants(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"id": variant_a, "weight": 25},
                        {"id": variant_b, "weight": 25.5},
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
                {"id": variant_a, "weight": 25},
                {"id": variant_b, "weight": 25.5},
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
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 25, variant_b: 25.5}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": mv_feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_override_enabled__creates_override(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_override_value__overrides_value(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__new_segment_override_without_state__inherits_environment_default_state(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"segment_overrides": [{"segment": {"id": segment}}]}),
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
    assert override.enabled is True
    assert override.get_feature_state_value() == "control"
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_overrides_without_priority__sets_priority_from_position(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.patch(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [segment_2],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_override_priority__writes_priority_as_given(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "priority": 5}]}
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
                "segment": {"id": segment_2},
                "priority": 1,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [],
            },
            {
                "segment": {"id": segment},
                "priority": 5,
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
    ) == {segment: 5, segment_2: 1}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [segment],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_override_priority_in_use__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "priority": 1}]}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {"detail": "Duplicate priority: 1."}
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .values_list("feature_segment__segment_id", "feature_segment__priority")
    ) == {segment: 0, segment_2: 1}
    assert log.events == []


def test_update_flag__patch_second_segment_override_without_priority__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "enabled": True}]}
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment_2}, "enabled": True}]}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {"detail": "Duplicate priority: 0."}
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .values_list("feature_segment__segment_id", "feature_segment__priority")
    ) == {segment: 0}
    assert log.events == []


def test_update_flag__patch_segment_overrides_swapping_priorities__reorders_overrides(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment_2}, "priority": 0},
                    {"segment": {"id": segment}, "priority": 1},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert [
        (override["segment"]["id"], override["priority"])
        for override in response.json()["segment_overrides"]
    ] == [(segment_2, 0), (segment, 1)]
    assert dict(
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .values_list("feature_segment__segment_id", "feature_segment__priority")
    ) == {segment: 1, segment_2: 0}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [segment_2, segment],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__patch_segment_override_variants__reweights_for_segment_only(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "variants": [
                            {"id": variant_a, "weight": 25},
                            {"id": variant_b, "weight": 25.5},
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
                {"id": variant_a, "weight": 10},
                {"id": variant_b, "weight": 20},
            ],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": False,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [
                    {"id": variant_a, "weight": 25},
                    {"id": variant_b, "weight": 25.5},
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
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 25, variant_b: 25.5}
    assert dict(
        live_feature_states.get(
            feature_segment=None
        ).multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 10, variant_b: 20}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": mv_feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__new_segment_override_without_variants__inherits_environment_default_variants(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants
    setup_response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"id": variant_a, "weight": 25},
                        {"id": variant_b, "weight": 25.5},
                    ],
                },
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    log.events.clear()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
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
            "variants": [
                {"id": variant_a, "weight": 25},
                {"id": variant_b, "weight": 25.5},
            ],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [
                    {"id": variant_a, "weight": 25},
                    {"id": variant_b, "weight": 25.5},
                ],
            },
        ],
    }
    override = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
    ).get(feature_segment__segment_id=segment)
    assert dict(
        override.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 25, variant_b: 25.5}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": mv_feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__put_segment_override_without_variants__inherits_environment_default_variants(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants
    setup_response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"id": variant_a, "weight": 25},
                        {"id": variant_b, "weight": 25.5},
                    ],
                },
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "enabled": True,
                        "variants": [
                            {"id": variant_a, "weight": 50},
                            {"id": variant_b, "weight": 0},
                        ],
                    },
                ],
            }
        ),
        format="json",
    )
    assert setup_response.status_code == 200
    log.events.clear()

    # When
    response = admin_client_new.put(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
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
            "variants": [
                {"id": variant_a, "weight": 25},
                {"id": variant_b, "weight": 25.5},
            ],
        },
        "segment_overrides": [
            {
                "segment": {"id": segment},
                "priority": 0,
                "enabled": True,
                "value": {"type": "string", "value": default_feature_value},
                "variants": [
                    {"id": variant_a, "weight": 25},
                    {"id": variant_b, "weight": 25.5},
                ],
            },
        ],
    }
    override = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
    ).get(feature_segment__segment_id=segment)
    assert dict(
        override.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 25, variant_b: 25.5}
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": mv_feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [segment],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__put_environment_default__replaces_environment_default(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.put(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__put_segment_overrides__replaces_segment_overrides(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.put(
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
                "enabled": True,
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [segment],
            "segment_overrides__deleted__segment__ids": [segment_2],
        },
    ]


def test_update_flag__put_environment_default_and_segment_overrides__replaces_both(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
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
    log.events.clear()

    # When
    response = admin_client_new.put(
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
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [segment_2],
        },
    ]


def test_update_flag__change_requests_enabled__responds_409(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given
    versioned_environment.minimum_change_request_approvals = 2
    versioned_environment.save()

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot update flags in an environment with change requests enabled.",
        "code": "change_requests_enabled",
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is False
    assert log.events == [
        {
            "level": "warning",
            "event": "flag.update_rejected",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "reason": "change_requests_enabled",
        },
    ]


def test_update_flag__value_not_matching_type__responds_400(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"environment_default": {"value": {"type": "integer", "value": "abc"}}}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {"value": ["'abc' is not a valid integer"]},
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.get_feature_state_value() == default_feature_value
    assert log.events == []


@pytest.mark.parametrize("body", [[], "segment_overrides"])
def test_update_flag__body_is_not_an_object__responds_400(
    admin_client_new: APIClient,
    body: object,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        body,
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == ["Expected an object."]
    assert log.events == []


def test_update_flag__unknown_feature__responds_404(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    unknown_feature = feature + 1

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{unknown_feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert log.events == []


def test_update_flag__unknown_environment__responds_404(
    admin_client_new: APIClient,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_client_new.patch(
        f"/api/__future__/environments/unknown-api-key/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert log.events == []


def test_update_flag__user_without_environment_permissions__responds_404(
    non_admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = non_admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is False
    assert log.events == []


def test_update_flag__unknown_segment__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    unknown_segment = segment + 1

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": unknown_segment}, "enabled": True},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "segment_overrides": [{"segment": {"id": ["Segment not found."]}}],
    }
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .exists()
    )
    assert log.events == []


def test_update_flag__duplicate_segment_overrides__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment}, "enabled": True},
                    {"segment": {"id": segment}, "enabled": False},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "segment_overrides": [f"Duplicate segment: {segment}."],
    }
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .exists()
    )
    assert log.events == []


def test_update_flag__segment_from_another_project__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment_in_other_project: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment_in_other_project}, "enabled": True},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "segment_overrides": [{"segment": {"id": ["Segment not found."]}}],
    }
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .exists()
    )
    assert log.events == []


def test_update_flag__update_feature_state_permission__gates_environment_default_only(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    organisation: int,
    segment: int,
    versioned_environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([UPDATE_FEATURE_STATE], environment, False)

    # When
    environment_default_response = staff_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )
    segment_overrides_response = staff_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment}, "enabled": True},
                ],
            }
        ),
        format="json",
    )

    # Then
    assert environment_default_response.status_code == 200
    assert segment_overrides_response.status_code == 403
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    assert live_feature_states.get(feature_segment=None).enabled is True
    assert not live_feature_states.exclude(feature_segment=None).exists()
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__manage_segment_overrides_permission__gates_segment_overrides_only(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    organisation: int,
    segment: int,
    versioned_environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES], environment, False)

    # When
    segment_overrides_response = staff_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment}, "enabled": True},
                ],
            }
        ),
        format="json",
    )
    environment_default_response = staff_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert segment_overrides_response.status_code == 200
    assert environment_default_response.status_code == 403
    live_feature_states = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    )
    override = live_feature_states.get(feature_segment__segment_id=segment)
    assert override.enabled is True
    assert live_feature_states.get(feature_segment=None).enabled is False
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [segment],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [],
        },
    ]


def test_update_flag__unknown_variant__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants
    unknown_variant = variant_b + 1

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"id": variant_a, "weight": 10},
                        {"id": unknown_variant, "weight": 20},
                    ],
                },
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {
            "variants": ["Variant not found."],
        },
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 10, variant_b: 20}
    assert log.events == []


def test_update_flag__variant_omitted__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {"environment_default": {"variants": [{"id": variant_a, "weight": 30}]}}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {
            "variants": ["Must include all feature's variants."],
        },
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 10, variant_b: 20}
    assert log.events == []


def test_update_flag__put_environment_default_without_variants__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants

    # When
    response = admin_client_new.put(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {
            "variants": ["Must include all feature's variants."],
        },
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
        feature_segment=None,
    ).get()
    assert environment_default.enabled is False
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 10, variant_b: 20}
    assert log.events == []


def test_update_flag__variant_weights_over_100__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    mv_feature: int,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, variant_b = mv_feature_variants

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{mv_feature}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "variants": [
                        {"id": variant_a, "weight": 60},
                        {"id": variant_b, "weight": 50},
                    ],
                },
            }
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {"variants": ["Total weight must not exceed 100."]},
    }
    environment_default = FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=mv_feature,
        feature_segment=None,
    ).get()
    assert dict(
        environment_default.multivariate_feature_state_values.values_list(
            "multivariate_feature_option_id", "percentage_allocation"
        )
    ) == {variant_a: 10, variant_b: 20}
    assert log.events == []


def test_update_flag__variants_on_standard_feature__responds_400(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    mv_feature_variants: list[int],
    versioned_environment: Environment,
) -> None:
    # Given
    variant_a, _ = mv_feature_variants

    # When
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"environment_default": {"variants": [{"id": variant_a, "weight": 10}]}}
        ),
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "environment_default": {"variants": ["Feature is not multivariate."]},
    }
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
            feature_segment=None,
        )
        .get()
        .multivariate_feature_state_values.exists()
    )
    assert log.events == []


@pytest.fixture()
def two_segment_overrides(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    versioned_environment: Environment,
) -> None:
    response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {
                "segment_overrides": [
                    {
                        "segment": {"id": segment},
                        "enabled": True,
                        "priority": 0,
                        "value": {"type": "string", "value": "enterprise"},
                    },
                    {
                        "segment": {"id": segment_2},
                        "enabled": True,
                        "priority": 1,
                        "value": {"type": "string", "value": "startup"},
                    },
                ],
            }
        ),
        format="json",
    )
    assert response.status_code == 200
    log.events.clear()


def test_delete_segment_override__existing_override__removes_override(
    admin_client_new: APIClient,
    default_feature_value: str,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    segment_2: int,
    two_segment_overrides: None,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
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
                "segment": {"id": segment_2},
                "priority": 1,
                "enabled": True,
                "value": {"type": "string", "value": "startup"},
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
    ) == {segment_2: 1}
    assert live_feature_states.get(feature_segment=None).enabled is False
    assert log.events == [
        {
            "level": "info",
            "event": "flag.updated",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "segment_overrides__created__segment__ids": [],
            "segment_overrides__updated__segment__ids": [],
            "segment_overrides__deleted__segment__ids": [segment],
        },
    ]


def test_delete_segment_override__last_override__removes_override(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    setup_response = admin_client_new.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/",
        UpdateFlagRequest(
            {"segment_overrides": [{"segment": {"id": segment}, "enabled": True}]}
        ),
        format="json",
    )
    assert setup_response.status_code == 200

    # When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 200
    assert response.json()["segment_overrides"] == []
    assert (
        not FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .exclude(feature_segment=None)
        .exists()
    )


def test_delete_segment_override__environment_versioned__publishes_new_version(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    two_segment_overrides: None,
    versioned_environment: Environment,
) -> None:
    # Given
    versions = EnvironmentFeatureVersion.objects.filter(
        environment=versioned_environment,
        feature_id=feature,
        published_at__isnull=False,
    )
    version_count = versions.count()

    # When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 200
    assert versions.count() == version_count + (
        1 if versioned_environment.use_v2_feature_versioning else 0
    )


def test_delete_segment_override__no_override__responds_404(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    versions = EnvironmentFeatureVersion.objects.filter(
        environment=versioned_environment, feature_id=feature
    )
    version_count = versions.count()

    # When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Segment override not found."}
    assert versions.count() == version_count
    assert log.events == []


def test_delete_segment_override__unknown_feature__responds_404(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given
    unknown_feature = feature + 1

    # When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}"
        f"/features/{unknown_feature}/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert log.events == []


def test_delete_segment_override__unknown_environment__responds_404(
    admin_client_new: APIClient,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = admin_client_new.delete(
        f"/api/__future__/environments/unknown-api-key/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert log.events == []


def test_delete_segment_override__change_requests_enabled__responds_409(
    admin_client_new: APIClient,
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    segment: int,
    two_segment_overrides: None,
    versioned_environment: Environment,
) -> None:
    # Given
    versioned_environment.minimum_change_request_approvals = 2
    versioned_environment.save()

    # When
    response = admin_client_new.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot update flags in an environment with change requests enabled.",
        "code": "change_requests_enabled",
    }
    assert (
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .filter(feature_segment__segment_id=segment)
        .exists()
    )
    assert log.events == [
        {
            "level": "warning",
            "event": "flag.update_rejected",
            "organisation__id": versioned_environment.project.organisation_id,
            "project__id": versioned_environment.project_id,
            "environment__id": versioned_environment.id,
            "feature__id": feature,
            "reason": "change_requests_enabled",
        },
    ]


def test_delete_segment_override__user_without_environment_permissions__responds_404(
    environment_api_key: str,
    feature: int,
    log: StructuredLogCapture,
    non_admin_client: APIClient,
    segment: int,
    two_segment_overrides: None,
    versioned_environment: Environment,
) -> None:
    # Given / When
    response = non_admin_client.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert (
        FeatureState.objects.get_live_feature_states(
            environment=versioned_environment,
            feature_id=feature,
        )
        .filter(feature_segment__segment_id=segment)
        .exists()
    )
    assert log.events == []


@pytest.mark.parametrize(
    "permission, expected_status_code",
    [
        pytest.param(MANAGE_SEGMENT_OVERRIDES, 200, id="manage_segment_overrides"),
        pytest.param(UPDATE_FEATURE_STATE, 403, id="update_feature_state"),
    ],
)
def test_delete_segment_override__environment_permission__gates_override(
    environment: int,
    environment_api_key: str,
    expected_status_code: int,
    feature: int,
    organisation: int,
    permission: str,
    segment: int,
    staff_client: APIClient,
    staff_user: FFAdminUser,
    two_segment_overrides: None,
    versioned_environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([permission], environment, False)

    # When
    response = staff_client.delete(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}"
        f"/segment-overrides/{segment}/",
    )

    # Then
    assert response.status_code == expected_status_code
    assert FeatureState.objects.get_live_feature_states(
        environment=versioned_environment,
        feature_id=feature,
    ).filter(feature_segment__segment_id=segment).exists() is (
        expected_status_code != 200
    )
