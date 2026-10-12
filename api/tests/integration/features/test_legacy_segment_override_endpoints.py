"""Segment override endpoints superseded by the flag API, but still in use.

TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
"""

from typing import Any

import pytest
from rest_framework.test import APIClient

from features.versioning.tasks import enable_v2_versioning

SYSTEM_SEGMENT_MODIFICATION_ERROR = {
    "code": "system_segment_modification",
    "message": (
        "System segments and their overrides can't be changed directly. "
        "Change this one through its flag dependency instead."
    ),
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
