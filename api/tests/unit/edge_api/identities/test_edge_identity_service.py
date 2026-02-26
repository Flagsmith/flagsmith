import uuid
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ObjectDoesNotExist
from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture

from edge_api.identities.edge_identity_service import (
    get_edge_identity_override_keys,
    get_overridden_feature_ids_for_edge_identity,
)
from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.utils import (
    get_environments_v2_identity_override_document_key,
)
from environments.models import Environment
from features.models import Feature
from util.mappers import map_environment_to_environment_v2_document


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
    _mock_ddb_identity_wrapper.get_item_from_uuid.return_value = identity_document

    # When
    result = get_overridden_feature_ids_for_edge_identity(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )

    # Then
    assert result == {feature_a_id, feature_b_id}
    _mock_ddb_identity_wrapper.get_item_from_uuid.assert_called_once_with(
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
    _mock_ddb_identity_wrapper.get_item_from_uuid.return_value = identity_document

    # When
    result = get_overridden_feature_ids_for_edge_identity(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )

    # Then
    assert result == set()


def test_get_overridden_feature_ids_for_edge_identity__nonexistent_identity__returns_empty_set(
    _mock_ddb_identity_wrapper: MagicMock,
) -> None:
    # Given
    _mock_ddb_identity_wrapper.get_item_from_uuid.side_effect = ObjectDoesNotExist()

    # When
    result = get_overridden_feature_ids_for_edge_identity(
        "59efa2a7-6a45-46d6-b953-a7073a90eacf"
    )

    # Then
    assert result == set()


def test_get_edge_identity_override_keys__returns_list_of_document_keys(
    flagsmith_environments_v2_table: Table,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    identity_uuid = str(uuid.uuid4())
    identifier = "identity1"
    document_key = get_environments_v2_identity_override_document_key(
        feature_id=feature.id, identity_uuid=identity_uuid
    )

    # TODO: this should be a fixture!
    override_document = {
        "environment_id": str(environment.id),
        "document_key": document_key,
        "environment_api_key": environment.api_key,
        "identifier": identifier,
        "feature_state": {},
    }

    environment_document = map_environment_to_environment_v2_document(environment)

    flagsmith_environments_v2_table.put_item(Item=override_document)
    flagsmith_environments_v2_table.put_item(Item=environment_document)

    # When
    document_keys = get_edge_identity_override_keys(environment_id=environment.id)

    # Then
    assert document_keys == [document_key]
