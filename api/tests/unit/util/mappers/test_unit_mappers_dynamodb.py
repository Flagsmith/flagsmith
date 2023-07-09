import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from util.mappers import dynamodb

if TYPE_CHECKING:  # pragma: no cover
    from pytest_mock import MockerFixture

    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment, EnvironmentAPIKey
    from features.models import FeatureState


def test_map_environment_to_environment_document__call_expected(
    environment: "Environment",
    feature_state: "FeatureState",
) -> None:
    # Given
    expected_api_key = environment.api_key
    expected_updated_at = environment.updated_at.isoformat()
    expected_featurestate_uuid = str(feature_state.uuid)

    # When
    result = dynamodb.map_environment_to_environment_document(environment)

    # Then
    assert result == {
        "allow_client_traits": True,
        "amplitude_config": None,
        "api_key": expected_api_key,
        "dynatrace_config": None,
        "feature_states": [
            {
                "django_id": Decimal(feature_state.pk),
                "enabled": False,
                "feature": {
                    "id": Decimal(feature_state.feature.pk),
                    "name": "Test Feature1",
                    "type": "STANDARD",
                },
                "feature_segment": None,
                "feature_state_value": None,
                "featurestate_uuid": expected_featurestate_uuid,
                "multivariate_feature_state_values": [],
            }
        ],
        "heap_config": None,
        "hide_disabled_flags": None,
        "hide_sensitive_data": False,
        "id": Decimal(environment.pk),
        "mixpanel_config": None,
        "name": "Test Environment",
        "project": {
            "enable_realtime_updates": False,
            "hide_disabled_flags": False,
            "id": Decimal(environment.project.pk),
            "name": "Test Project",
            "organisation": {
                "feature_analytics": False,
                "id": Decimal(environment.project.organisation.pk),
                "name": "Test Org",
                "persist_trait_data": True,
                "stop_serving_flags": False,
            },
            "segments": [],
            "server_key_only_feature_ids": [],
        },
        "rudderstack_config": None,
        "segment_config": None,
        "updated_at": expected_updated_at,
        "use_identity_composite_key_for_hashing": True,
        "webhook_config": None,
    }


def test_map_environment_api_key_to_environment_api_key_document__call_expected(
    environment_api_key: "EnvironmentAPIKey",
) -> None:
    # Given
    expected_client_api_key = environment_api_key.environment.api_key
    expected_created_at = environment_api_key.created_at.isoformat()
    expected_key = environment_api_key.key

    # When
    result = dynamodb.map_environment_api_key_to_environment_api_key_document(
        environment_api_key,
    )

    # Then
    assert result == {
        "active": True,
        "client_api_key": expected_client_api_key,
        "created_at": expected_created_at,
        "expires_at": None,
        "id": Decimal(environment_api_key.pk),
        "key": expected_key,
        "name": "Test API Key",
    }


def test_map_identity_to_identity_document__call_expected(
    identity: "Identity",
    trait: "Trait",
    mocker: "MockerFixture",
) -> None:
    # Given
    expected_composite_key = identity.composite_key
    expected_created_date = identity.created_date.isoformat()
    expected_environment_api_key = identity.environment.api_key

    # When
    result = dynamodb.map_identity_to_identity_document(
        identity,
    )

    # Then
    assert result == {
        "composite_key": expected_composite_key,
        "created_date": expected_created_date,
        "django_id": Decimal(identity.pk),
        "environment_api_key": expected_environment_api_key,
        "identifier": "test_identity",
        "identity_features": [],
        "identity_traits": [{"trait_key": "key1", "trait_value": "value1"}],
        "identity_uuid": mocker.ANY,
    }
    assert uuid.UUID(result["identity_uuid"])
