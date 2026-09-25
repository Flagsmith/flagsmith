import gzip
import json
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.utils import timezone

from environments.dynamodb.constants import (
    ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
)
from util.mappers import dynamodb
from util.mappers.engine import map_feature_state_to_engine, map_identifier_to_engine

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment, EnvironmentAPIKey
    from experimentation.models import Experiment
    from features.models import Feature, FeatureState


def test_map_environment_to_environment_document__valid_environment__returns_expected_document(
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
        "onboarding_pending": True,
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
        "use_identity_overrides_in_local_eval": True,
        "webhook_config": None,
    }


def test_map_environment_to_environment_document__first_evaluated__onboarding_pending_false(
    environment: "Environment",
) -> None:
    # Given
    environment.first_evaluated_at = timezone.now()
    environment.save(update_fields=["first_evaluated_at"])

    # When
    result = dynamodb.map_environment_to_environment_document(environment)

    # Then
    assert result["onboarding_pending"] is False


def test_map_environment_api_key_to_environment_api_key_document__valid_key__returns_expected_document(
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


def test_map_identity_to_identity_document__valid_identity__returns_expected_document(
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
    assert uuid.UUID(result["identity_uuid"])  # type: ignore[arg-type]


def test_map_engine_identity_to_identity_document__system_traits_set__included_in_document() -> (
    None
):
    # Given
    engine_identity = map_identifier_to_engine(
        "test_identity", "api-key", system_traits={"flagsmith_cohort_2b6d1f5f": True}
    )

    # When
    result = dynamodb.map_engine_identity_to_identity_document(engine_identity)

    # Then
    assert result["system_traits"] == {"flagsmith_cohort_2b6d1f5f": True}


def test_map_engine_identity_to_identity_document__no_system_traits__key_absent() -> (
    None
):
    # Given
    engine_identity = map_identifier_to_engine("test_identity", "api-key")

    # When
    result = dynamodb.map_engine_identity_to_identity_document(engine_identity)

    # Then
    assert "system_traits" not in result


def test_identity_document__system_traits_set__round_trip_preserves_system_traits() -> (
    None
):
    # Given
    document = dynamodb.map_engine_identity_to_identity_document(
        map_identifier_to_engine(
            "test_identity",
            "api-key",
            system_traits={"flagsmith_cohort_2b6d1f5f": True},
        )
    )

    # When
    parsed = dynamodb.map_identity_document_to_engine_identity(document)

    # Then
    assert parsed["system_traits"] == {"flagsmith_cohort_2b6d1f5f": True}


def test_map_engine_identity_to_identity_document__stored_numbers__round_trip_unchanged() -> (
    None
):
    # Given
    stored_document = dynamodb.map_engine_identity_to_identity_document(
        map_identifier_to_engine(
            "test_identity",
            "api-key",
            identity_traits=[
                {"trait_key": "integer", "trait_value": 1},
                {"trait_key": "float", "trait_value": 1.5},
            ],
            identity_features=[
                {
                    "feature": {"id": 1, "name": "feature", "type": "MULTIVARIATE"},
                    "enabled": True,
                    "feature_state_value": 5,
                    "featurestate_uuid": str(uuid.uuid4()),
                    "multivariate_feature_state_values": [
                        {
                            "mv_fs_value_uuid": str(uuid.uuid4()),
                            "percentage_allocation": 100,
                            "multivariate_feature_option": {"id": 2, "value": 3},
                        }
                    ],
                }
            ],
        )
    )

    # When
    document: dict[str, Any] = dynamodb.map_engine_identity_to_identity_document(
        dynamodb.map_identity_document_to_engine_identity(stored_document)
    )

    # Then
    assert document == stored_document
    assert document["identity_traits"] == [
        {"trait_key": "integer", "trait_value": Decimal("1")},
        {"trait_key": "float", "trait_value": Decimal("1.5")},
    ]
    (feature_state,) = document["identity_features"]
    assert feature_state["feature_state_value"] == Decimal("5")
    assert feature_state["multivariate_feature_state_values"][0][
        "multivariate_feature_option"
    ]["value"] == Decimal("3")


def test_map_environment_to_environment_v2_document__valid_environment__returns_expected_document(
    environment: "Environment",
    feature_state: "FeatureState",
) -> None:
    # Given
    expected_api_key = environment.api_key
    expected_updated_at = environment.updated_at.isoformat()
    expected_featurestate_uuid = str(feature_state.uuid)

    # When
    result = dynamodb.map_environment_to_environment_v2_document(environment)

    # Then
    assert result == {
        "document_key": ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
        "environment_id": str(environment.id),
        "environment_api_key": expected_api_key,
        "allow_client_traits": True,
        "amplitude_config": None,
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
        "onboarding_pending": True,
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
        "use_identity_overrides_in_local_eval": True,
        "webhook_config": None,
    }


def test_map_identity_override_to_identity_override_document__decimal_feature_state_value__returns_string_value(
    identity: "Identity",
    identity_featurestate: "FeatureState",
) -> None:
    # Given
    feature_state_value = Decimal("1.111")

    engine_feature_state = {
        **map_feature_state_to_engine(identity_featurestate),
        "feature_state_value": feature_state_value,
    }
    identity_override = dynamodb.map_engine_feature_state_to_identity_override(
        feature_state=engine_feature_state,
        identity_uuid=str(uuid.uuid4()),
        identifier=identity.identifier,
        environment_api_key=identity.environment.api_key,
        environment_id=identity.environment.id,
    )

    # When
    result = dynamodb.map_identity_override_to_identity_override_document(
        identity_override
    )

    # Then
    feature_state = result["feature_state"]
    assert isinstance(feature_state, dict)
    assert feature_state["feature_state_value"] == "1.111"


def test_map_environment_to_compressed_environment_document__valid_environment__returns_compressed_fields(
    environment: "Environment",
    feature_state: "FeatureState",
) -> None:
    # Given
    uncompressed_document = dynamodb.map_environment_to_environment_document(
        environment
    )

    # When
    result = dynamodb.map_environment_to_compressed_environment_document(environment)

    # Then
    assert result.compressed_size_bytes > 0
    assert 0 < result.compression_ratio < 1.0

    compressed_project = result.document["project"]
    compressed_feature_states = result.document["feature_states"]
    assert isinstance(compressed_project, bytes)
    assert isinstance(compressed_feature_states, bytes)
    assert (
        json.loads(gzip.decompress(compressed_project).decode("utf-8"))
        == uncompressed_document["project"]
    )
    assert (
        json.loads(gzip.decompress(compressed_feature_states).decode("utf-8"))
        == uncompressed_document["feature_states"]
    )


def test_map_environment_to_compressed_environment_document__not_evaluated__onboarding_pending_retained(
    environment: "Environment",
) -> None:
    # Given
    assert environment.first_evaluated_at is None

    # When
    result = dynamodb.map_environment_to_compressed_environment_document(environment)

    # Then
    assert result.document["onboarding_pending"] is True


def test_map_environment_to_compressed_environment_document__mv_option_with_key__key_preserved(
    environment: "Environment",
    multivariate_feature: "Feature",
) -> None:
    # Given
    mv_option = multivariate_feature.multivariate_options.first()
    assert mv_option is not None
    mv_option.key = "control"
    mv_option.save()

    # When
    result = dynamodb.map_environment_to_compressed_environment_document(environment)

    # Then
    compressed_feature_states = result.document["feature_states"]
    assert isinstance(compressed_feature_states, bytes)
    feature_states = json.loads(
        gzip.decompress(compressed_feature_states).decode("utf-8")
    )
    mv_options = [
        mv_value["multivariate_feature_option"]
        for feature_state in feature_states
        for mv_value in feature_state["multivariate_feature_state_values"]
    ]
    keyed_option = next(option for option in mv_options if option["id"] == mv_option.id)
    assert keyed_option["key"] == "control"


def test_map_environment_to_compressed_environment_v2_document__valid_environment__returns_compressed_fields(
    environment: "Environment",
    feature_state: "FeatureState",
) -> None:
    # Given
    uncompressed_document = dynamodb.map_environment_to_environment_v2_document(
        environment
    )

    # When
    result = dynamodb.map_environment_to_compressed_environment_v2_document(environment)

    # Then
    assert result.compressed_size_bytes > 0
    assert 0 < result.compression_ratio < 1.0

    compressed_project = result.document["project"]
    compressed_feature_states = result.document["feature_states"]
    assert isinstance(compressed_project, bytes)
    assert isinstance(compressed_feature_states, bytes)
    assert (
        json.loads(gzip.decompress(compressed_project).decode("utf-8"))
        == uncompressed_document["project"]
    )
    assert (
        json.loads(gzip.decompress(compressed_feature_states).decode("utf-8"))
        == uncompressed_document["feature_states"]
    )


def test_map_environment_to_compressed_environment_document__running_experiment__metadata_preserved(
    environment: "Environment",
    running_experiment: "Experiment",
) -> None:
    # Given
    expected_metadata = {
        "experiment": {
            "id": running_experiment.id,
            "name": "New checkout CTA",
            "in_experiment": False,
        }
    }

    # When
    result = dynamodb.map_environment_to_compressed_environment_document(environment)

    # Then
    compressed_feature_states = result.document["feature_states"]
    assert isinstance(compressed_feature_states, bytes)
    feature_states = json.loads(gzip.decompress(compressed_feature_states))
    assert feature_states[0]["metadata"] == expected_metadata
