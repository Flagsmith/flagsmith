"""Segment override endpoints superseded by the flag API, but still in use.

TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
"""

from typing import Any
from unittest import mock

import pytest
from rest_framework.test import APIClient

from features.versioning.tasks import enable_v2_versioning

SYSTEM_SEGMENT_MODIFICATION_ERROR = {
    "detail": "System segments and their overrides can't be changed directly.",
    "code": "system_segment_modification",
}


def _get_segment_overrides(
    admin_client: APIClient, environment_api_key: str, feature: int
) -> list[dict[str, Any]]:
    response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature}/"
    )
    assert response.status_code == 200
    segment_overrides: list[dict[str, Any]] = response.json()["segment_overrides"]
    return segment_overrides


def _get_feature_segment_id(
    admin_client: APIClient, environment: int, feature: int, segment: int
) -> int:
    response = admin_client.get(
        "/api/v1/features/feature-segments/",
        data={"environment": environment, "feature": feature},
    )
    [feature_segment_id] = [
        result["id"]
        for result in response.json()["results"]
        if result["segment"] == segment
    ]
    return int(feature_segment_id)


def _get_segment_override_id(
    admin_client: APIClient, environment: int, feature: int, segment: int
) -> int:
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, segment
    )
    response = admin_client.get(
        "/api/v1/features/featurestates/",
        data={"environment": environment, "feature": feature},
    )
    [segment_override_id] = [
        result["id"]
        for result in response.json()["results"]
        if result["feature_segment"] == feature_segment_id
    ]
    return int(segment_override_id)


def _create_segment(admin_client: APIClient, project: int, name: str) -> int:
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        {
            "name": name,
            "project": project,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )
    assert response.status_code == 201
    return int(response.json()["id"])


@pytest.fixture()
def system_segment(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    feature_2: int,
) -> int:
    """A system segment the feature is overridden for, by depending on another."""
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        f"/dependencies/{feature_2}/",
    )
    assert response.status_code == 201
    return int(response.json()["segment"]["id"])


@pytest.fixture()
def other_environment(admin_client: APIClient, project: int) -> dict[str, Any]:
    response = admin_client.post(
        "/api/v1/environments/",
        data={"name": "Other Environment", "project": project},
        format="json",
    )
    assert response.status_code == 201
    environment: dict[str, Any] = response.json()
    return environment


def test_create_segment_override__new_segment__appends_override(
    admin_client: APIClient,
    default_feature_value: str,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
    system_segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        "/create-segment-override/",
        {
            "feature_segment": {"segment": segment},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    assert response.json() == {
        "id": _get_segment_override_id(admin_client, environment, feature, segment),
        "uuid": mock.ANY,
        "feature_segment": {
            "id": _get_feature_segment_id(admin_client, environment, feature, segment),
            "uuid": mock.ANY,
            "segment": segment,
            "priority": 1,
        },
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
            "integer_value": None,
            "boolean_value": None,
        },
        "multivariate_feature_state_values": [],
        "deleted_at": None,
        "created_at": mock.ANY,
        "updated_at": mock.ANY,
        "live_from": mock.ANY,
        "environment": environment,
        "feature": feature,
        "identity": None,
        "change_request": None,
    }
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == [
        {
            "segment": {"id": system_segment},
            "priority": 0,
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
        {
            "segment": {"id": segment},
            "priority": 1,
            "enabled": True,
            "value": {"type": "string", "value": "foo"},
            "variants": [],
        },
    ]


def test_create_segment_override__existing_override__updates_override(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
) -> None:
    # Given
    url = (
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        "/create-segment-override/"
    )
    admin_client.post(
        url,
        {
            "feature_segment": {"segment": segment},
            "enabled": False,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # When
    response = admin_client.post(
        url,
        {
            "feature_segment": {"segment": segment},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "bar"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == [
        {
            "segment": {"id": segment},
            "priority": 0,
            "enabled": True,
            "value": {"type": "string", "value": "bar"},
            "variants": [],
        },
    ]


def test_create_segment_override__priority_in_use__responds_400(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    segment: int,
    system_segment: int,
) -> None:
    # Given
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        "/create-segment-override/",
        {
            "feature_segment": {"segment": segment, "priority": 0},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {"detail": "Duplicate priority: 0."}
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_create_segment_override__system_segment__responds_409(
    admin_client: APIClient,
    environment_api_key: str,
    feature: int,
    system_segment: int,
) -> None:
    # Given
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        "/create-segment-override/",
        {
            "feature_segment": {"segment": system_segment},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_create_feature_segment_then_feature_state__new_segment__creates_override(
    admin_client: APIClient,
    default_feature_value: str,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
) -> None:
    """The flow of the Flagsmith Go API client, and Terraform provider."""
    # Given / When
    feature_segment_response = admin_client.post(
        "/api/v1/features/feature-segments/",
        {"feature": feature, "segment": segment, "environment": environment},
        format="json",
    )
    feature_segment_overrides = _get_segment_overrides(
        admin_client, environment_api_key, feature
    )
    feature_state_response = admin_client.post(
        "/api/v1/features/featurestates/",
        {
            "feature": feature,
            "environment": environment,
            "feature_segment": feature_segment_response.json()["id"],
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert feature_segment_response.status_code == 201
    assert feature_segment_response.json() == {
        "id": mock.ANY,
        "uuid": mock.ANY,
        "feature": feature,
        "segment": segment,
        "environment": environment,
        "priority": 0,
    }
    assert feature_segment_overrides == [
        {
            "segment": {"id": segment},
            "priority": 0,
            "enabled": False,
            "value": {"type": "string", "value": default_feature_value},
            "variants": [],
        },
    ]
    assert feature_state_response.status_code == 201
    assert feature_state_response.json() == {
        "id": _get_segment_override_id(admin_client, environment, feature, segment),
        "uuid": mock.ANY,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
            "integer_value": None,
            "boolean_value": None,
        },
        "multivariate_feature_state_values": [],
        "enabled": True,
        "deleted_at": None,
        "created_at": mock.ANY,
        "updated_at": mock.ANY,
        "live_from": mock.ANY,
        "version": 1,
        "feature": feature,
        "environment": environment,
        "identity": None,
        "feature_segment": feature_segment_response.json()["id"],
        "change_request": None,
        "environment_feature_version": None,
    }
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == [
        {
            "segment": {"id": segment},
            "priority": 0,
            "enabled": True,
            "value": {"type": "string", "value": "foo"},
            "variants": [],
        },
    ]


def test_create_feature_segment__existing_override__responds_400(
    admin_client: APIClient,
    environment: int,
    feature: int,
    system_segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        "/api/v1/features/feature-segments/",
        {"feature": feature, "segment": system_segment, "environment": environment},
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == ["The flag is already overridden for this segment."]


def test_create_feature_segment__system_segment__responds_409(
    admin_client: APIClient,
    feature: int,
    other_environment: dict[str, Any],
    system_segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        "/api/v1/features/feature-segments/",
        {
            "feature": feature,
            "segment": system_segment,
            "environment": other_environment["id"],
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert (
        _get_segment_overrides(admin_client, other_environment["api_key"], feature)
        == []
    )


def test_update_feature_segment__system_segment__responds_409(
    admin_client: APIClient,
    environment: int,
    feature: int,
    segment: int,
    system_segment: int,
) -> None:
    # Given
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, system_segment
    )

    # When
    response = admin_client.put(
        f"/api/v1/features/feature-segments/{feature_segment_id}/",
        {"feature": feature, "segment": segment, "environment": environment},
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR


@pytest.mark.parametrize("v2_versioning", [False, True])
def test_delete_feature_segment__live_override__removes_override(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
    v2_versioning: bool,
) -> None:
    # Given
    if v2_versioning:
        enable_v2_versioning(environment_id=environment)
    create_segment_override(environment_api_key, feature, segment)
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, segment
    )

    # When
    response = admin_client.delete(
        f"/api/v1/features/feature-segments/{feature_segment_id}/"
    )

    # Then
    assert response.status_code == 204
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == []


@pytest.mark.parametrize("v2_versioning", [False, True])
def test_delete_feature_segment__system_segment__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
    v2_versioning: bool,
) -> None:
    # Given
    if v2_versioning:
        enable_v2_versioning(environment_id=environment)
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, system_segment
    )

    # When
    response = admin_client.delete(
        f"/api/v1/features/feature-segments/{feature_segment_id}/"
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_update_feature_state__live_override__updates_override(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
) -> None:
    # Given
    create_segment_override(environment_api_key, feature, segment)
    feature_state_id = _get_segment_override_id(
        admin_client, environment, feature, segment
    )

    # When
    response = admin_client.patch(
        f"/api/v1/features/featurestates/{feature_state_id}/",
        {
            "feature": feature,
            "environment": environment,
            "enabled": False,
            "feature_state_value": {"type": "int", "integer_value": 42},
        },
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "id": feature_state_id,
        "uuid": mock.ANY,
        "feature_state_value": {
            "type": "int",
            "string_value": None,
            "integer_value": 42,
            "boolean_value": None,
        },
        "multivariate_feature_state_values": [],
        "enabled": False,
        "deleted_at": None,
        "created_at": mock.ANY,
        "updated_at": mock.ANY,
        "live_from": mock.ANY,
        "version": 1,
        "feature": feature,
        "environment": environment,
        "identity": None,
        "feature_segment": _get_feature_segment_id(
            admin_client, environment, feature, segment
        ),
        "change_request": None,
        "environment_feature_version": None,
    }
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == [
        {
            "segment": {"id": segment},
            "priority": 0,
            "enabled": False,
            "value": {"type": "integer", "value": "42"},
            "variants": [],
        },
    ]


def test_update_feature_state__system_segment_override_as_read__responds_200(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
) -> None:
    """The dashboard writes every override of flags it saves."""
    # Given
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)
    url = (
        "/api/v1/features/featurestates/"
        f"{_get_segment_override_id(admin_client, environment, feature, system_segment)}/"
    )
    feature_state = admin_client.get(
        "/api/v1/features/featurestates/",
        data={"environment": environment, "feature": feature},
    ).json()["results"]
    [system_segment_override] = [
        result for result in feature_state if result["id"] == int(url.split("/")[-2])
    ]

    # When
    response = admin_client.put(url, system_segment_override, format="json")

    # Then
    assert response.status_code == 200
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_update_feature_state__system_segment_override_changed__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
) -> None:
    # Given
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)
    feature_state_id = _get_segment_override_id(
        admin_client, environment, feature, system_segment
    )

    # When
    response = admin_client.patch(
        f"/api/v1/features/featurestates/{feature_state_id}/",
        {"feature": feature, "environment": environment, "enabled": True},
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


@pytest.mark.parametrize("v2_versioning", [False, True])
def test_update_priorities__one_override_moved_up__moves_others_down(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    project: int,
    v2_versioning: bool,
) -> None:
    """The Flagsmith Go API client, and Terraform provider, move one at a time."""
    # Given
    if v2_versioning:
        enable_v2_versioning(environment_id=environment)
    segments = [
        _create_segment(admin_client, project, f"segment {i}") for i in range(3)
    ]
    for priority, segment in enumerate(segments):
        create_segment_override(
            environment_api_key, feature, segment, priority=priority
        )
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, segments[2]
    )

    # When
    response = admin_client.post(
        "/api/v1/features/feature-segments/update-priorities/",
        [{"id": feature_segment_id, "priority": 0}],
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": _get_feature_segment_id(
                admin_client, environment, feature, segments[2]
            ),
            "uuid": mock.ANY,
            "segment": segments[2],
            "priority": 0,
            "environment": environment,
            "segment_name": "segment 2",
            "is_feature_specific": False,
            "is_system_segment": False,
            "segment_managed_by": "",
        },
    ]
    assert [
        (override["segment"]["id"], override["priority"])
        for override in _get_segment_overrides(
            admin_client, environment_api_key, feature
        )
    ] == [(segments[2], 0), (segments[0], 1), (segments[1], 2)]


def test_update_priorities__system_segment_override_moved__responds_409(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
    system_segment: int,
) -> None:
    # Given
    create_segment_override(environment_api_key, feature, segment, priority=1)
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)

    # When
    response = admin_client.post(
        "/api/v1/features/feature-segments/update-priorities/",
        [
            {
                "id": _get_feature_segment_id(
                    admin_client, environment, feature, segment
                ),
                "priority": 0,
            }
        ],
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_update_priorities__system_segment_override_kept__reorders_others(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    project: int,
    system_segment: int,
) -> None:
    """The dashboard sends the priorities of every override when reordering."""
    # Given
    segments = [
        _create_segment(admin_client, project, f"segment {i}") for i in range(2)
    ]
    for priority, segment in enumerate(segments, start=1):
        create_segment_override(
            environment_api_key, feature, segment, priority=priority
        )

    # When
    response = admin_client.post(
        "/api/v1/features/feature-segments/update-priorities/",
        [
            {
                "id": _get_feature_segment_id(
                    admin_client, environment, feature, segment
                ),
                "priority": priority,
            }
            for segment, priority in [
                (system_segment, 0),
                (segments[1], 1),
                (segments[0], 2),
            ]
        ],
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert [
        (override["segment"]["id"], override["priority"])
        for override in _get_segment_overrides(
            admin_client, environment_api_key, feature
        )
    ] == [(system_segment, 0), (segments[1], 1), (segments[0], 2)]


def test_create_environment_feature_state__system_segment__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/featurestates/",
        {
            "feature": feature,
            "feature_segment": _get_feature_segment_id(
                admin_client, environment, feature, system_segment
            ),
            "enabled": True,
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR


@pytest.mark.parametrize(
    "version_changes",
    [
        {
            "feature_states_to_update": [
                {
                    "feature_segment": {"segment": "system_segment"},
                    "enabled": True,
                    "feature_state_value": {"type": "unicode", "string_value": "foo"},
                }
            ]
        },
        {"segment_ids_to_delete_overrides": ["system_segment"]},
    ],
)
def test_create_version__system_segment_override_changed__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
    version_changes: dict[str, Any],
) -> None:
    # Given
    enable_v2_versioning(environment_id=environment)
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)
    data = {
        key: [
            {**value, "feature_segment": {"segment": system_segment}}
            if isinstance(value, dict)
            else system_segment
            for value in values
        ]
        for key, values in version_changes.items()
    }

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment}/features/{feature}/versions/",
        {**data, "publish_immediately": True},
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_create_version__new_system_segment_override__responds_409(
    admin_client: APIClient,
    feature: int,
    other_environment: dict[str, Any],
    system_segment: int,
) -> None:
    # Given
    enable_v2_versioning(environment_id=other_environment["id"])

    # When
    response = admin_client.post(
        f"/api/v1/environments/{other_environment['id']}/features/{feature}/versions/",
        {
            "feature_states_to_create": [
                {
                    "feature_segment": {"segment": system_segment},
                    "enabled": True,
                    "feature_state_value": {"type": "unicode", "string_value": "foo"},
                }
            ],
            "publish_immediately": True,
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert (
        _get_segment_overrides(admin_client, other_environment["api_key"], feature)
        == []
    )


@pytest.mark.parametrize("method", ["put", "delete"])
def test_write_draft_version_feature_state__system_segment__responds_409(
    admin_client: APIClient,
    environment: int,
    feature: int,
    method: str,
    system_segment: int,
) -> None:
    # Given
    enable_v2_versioning(environment_id=environment)
    version_uuid = admin_client.post(
        f"/api/v1/environments/{environment}/features/{feature}/versions/",
        {},
        format="json",
    ).json()["uuid"]
    url = (
        f"/api/v1/environments/{environment}/features/{feature}"
        f"/versions/{version_uuid}/featurestates/"
    )
    [system_segment_override] = [
        feature_state
        for feature_state in admin_client.get(url).json()
        if feature_state["feature_segment"]
        and feature_state["feature_segment"]["segment"] == system_segment
    ]

    # When
    response = getattr(admin_client, method)(
        f"{url}{system_segment_override['id']}/",
        {**system_segment_override, "enabled": True},
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR


def test_create_draft_version_feature_state__system_segment__responds_409(
    admin_client: APIClient,
    feature: int,
    other_environment: dict[str, Any],
    system_segment: int,
) -> None:
    # Given
    environment = other_environment["id"]
    enable_v2_versioning(environment_id=environment)
    version_uuid = admin_client.post(
        f"/api/v1/environments/{environment}/features/{feature}/versions/",
        {},
        format="json",
    ).json()["uuid"]

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment}/features/{feature}"
        f"/versions/{version_uuid}/featurestates/",
        {
            "feature_segment": {"segment": system_segment},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR


def test_create_segment_override__no_feature_segment__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        "/create-segment-override/",
        {
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {"feature_segment": ["This field is required."]}


def test_update_feature_segment__to_system_segment__responds_409(
    admin_client: APIClient,
    feature: int,
    other_environment: dict[str, Any],
    segment: int,
    system_segment: int,
) -> None:
    # Given
    feature_segment_id = admin_client.post(
        "/api/v1/features/feature-segments/",
        {
            "feature": feature,
            "segment": segment,
            "environment": other_environment["id"],
        },
        format="json",
    ).json()["id"]

    # When
    response = admin_client.put(
        f"/api/v1/features/feature-segments/{feature_segment_id}/",
        {
            "feature": feature,
            "segment": system_segment,
            "environment": other_environment["id"],
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR


def test_update_feature_state__value_cleared__clears_override_value(
    admin_client: APIClient,
    create_segment_override: Any,
    environment: int,
    environment_api_key: str,
    feature: int,
    segment: int,
) -> None:
    # Given
    create_segment_override(environment_api_key, feature, segment)
    feature_state_id = _get_segment_override_id(
        admin_client, environment, feature, segment
    )

    # When
    response = admin_client.put(
        f"/api/v1/features/featurestates/{feature_state_id}/",
        {
            "feature": feature,
            "environment": environment,
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": None},
        },
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == [
        {
            "segment": {"id": segment},
            "priority": 0,
            "enabled": True,
            "value": None,
            "variants": [],
        },
    ]


def test_update_feature_state__system_segment_override_scheduled__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    system_segment: int,
) -> None:
    # Given
    overrides = _get_segment_overrides(admin_client, environment_api_key, feature)
    feature_state_id = _get_segment_override_id(
        admin_client, environment, feature, system_segment
    )

    # When
    response = admin_client.put(
        f"/api/v1/features/featurestates/{feature_state_id}/",
        {
            "feature": feature,
            "environment": environment,
            "enabled": True,
            "live_from": "2099-01-01T00:00:00Z",
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
    assert _get_segment_overrides(admin_client, environment_api_key, feature) == (
        overrides
    )


def test_update_priorities__priorities_as_they_are__responds_200(
    admin_client: APIClient,
    environment: int,
    feature: int,
    system_segment: int,
) -> None:
    # Given
    feature_segment_id = _get_feature_segment_id(
        admin_client, environment, feature, system_segment
    )

    # When
    response = admin_client.post(
        "/api/v1/features/feature-segments/update-priorities/",
        [{"id": feature_segment_id, "priority": 0}],
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": feature_segment_id,
            "uuid": mock.ANY,
            "segment": system_segment,
            "priority": 0,
            "environment": environment,
            "segment_name": "feature_1-depends-on-feature_2",
            "is_feature_specific": True,
            "is_system_segment": True,
            "segment_managed_by": "dependency",
        },
    ]


def test_update_draft_version_feature_state__to_system_segment__responds_409(
    admin_client: APIClient,
    feature: int,
    other_environment: dict[str, Any],
    segment: int,
    system_segment: int,
) -> None:
    # Given
    environment = other_environment["id"]
    enable_v2_versioning(environment_id=environment)
    version_uuid = admin_client.post(
        f"/api/v1/environments/{environment}/features/{feature}/versions/",
        {},
        format="json",
    ).json()["uuid"]
    url = (
        f"/api/v1/environments/{environment}/features/{feature}"
        f"/versions/{version_uuid}/featurestates/"
    )
    feature_state = admin_client.post(
        url,
        {
            "feature_segment": {"segment": segment},
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foo"},
        },
        format="json",
    ).json()

    # When
    response = admin_client.put(
        f"{url}{feature_state['id']}/",
        {
            **feature_state,
            "feature_segment": {
                **feature_state["feature_segment"],
                "segment": system_segment,
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == SYSTEM_SEGMENT_MODIFICATION_ERROR
