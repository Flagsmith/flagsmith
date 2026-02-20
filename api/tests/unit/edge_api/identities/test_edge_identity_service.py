from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from edge_api.identities.edge_identity_service import (
    get_overridden_feature_ids_for_edge_identity,
)


@pytest.fixture()
def _mock_ddb_identity_wrapper(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )


def _make_identity_document(
    *,
    environment_api_key: str,
    identity_features: list[dict],  # type: ignore[type-arg]
) -> dict:  # type: ignore[type-arg]
    return {
        "composite_key": f"{environment_api_key}_test_user",
        "identity_traits": [],
        "identity_features": identity_features,
        "identifier": "test_user",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment_api_key,
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
        "django_id": None,
    }


def test_get_overridden_feature_ids_for_edge_identity__identity_with_overrides__returns_feature_ids(
    _mock_ddb_identity_wrapper: MagicMock,
) -> None:
    # Given
    feature_a_id = 101
    feature_b_id = 202
    identity_document = _make_identity_document(
        environment_api_key="test_key",
        identity_features=[
            {
                "feature": {
                    "id": feature_a_id,
                    "name": "feature_a",
                    "type": "STANDARD",
                },
                "enabled": True,
                "featurestate_uuid": "a7495917-ee57-41d1-a64e-e0697dbc57fb",
                "feature_state_value": None,
                "feature_segment": None,
                "multivariate_feature_state_values": [],
            },
            {
                "feature": {
                    "id": feature_b_id,
                    "name": "feature_b",
                    "type": "STANDARD",
                },
                "enabled": False,
                "featurestate_uuid": "b8506028-ff68-42e2-b75f-f1708ecd68fc",
                "feature_state_value": None,
                "feature_segment": None,
                "multivariate_feature_state_values": [],
            },
        ],
    )
    _mock_ddb_identity_wrapper.get_item_from_uuid_or_404.return_value = (
        identity_document
    )

    # When
    result = get_overridden_feature_ids_for_edge_identity(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )

    # Then
    assert result == {feature_a_id, feature_b_id}
    _mock_ddb_identity_wrapper.get_item_from_uuid_or_404.assert_called_once_with(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )


def test_get_overridden_feature_ids_for_edge_identity__identity_without_overrides__returns_empty_set(
    _mock_ddb_identity_wrapper: MagicMock,
) -> None:
    # Given
    identity_document = _make_identity_document(
        environment_api_key="test_key",
        identity_features=[],
    )
    _mock_ddb_identity_wrapper.get_item_from_uuid_or_404.return_value = (
        identity_document
    )

    # When
    result = get_overridden_feature_ids_for_edge_identity(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )

    # Then
    assert result == set()
