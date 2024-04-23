from typing import TYPE_CHECKING

import pytest

from environments.identities.models import Identity
from util.mappers.sdk import map_environment_to_sdk_document

if TYPE_CHECKING:  # pragma: no cover
    from pytest_mock import MockerFixture

    from environments.models import Environment
    from features.models import FeatureState


@pytest.fixture()
def identity_without_overrides(environment):
    return Identity.objects.create(
        identifier="test_identity_without_overrides", environment=environment
    )


def test_map_environment_to_sdk_document__return_expected(
    mocker: "MockerFixture",
    environment: "Environment",
    feature_state: "FeatureState",
    identity: Identity,
    identity_featurestate: "FeatureState",
    identity_without_overrides: Identity,
) -> None:
    # Given
    expected_overridden_value = "some-overridden-value"
    expected_api_key = environment.api_key

    identity_featurestate.feature_state_value.string_value = expected_overridden_value
    identity_featurestate.feature_state_value.save()
    identity_featurestate.enabled = True
    identity_featurestate.save()

    # When
    result = map_environment_to_sdk_document(environment)

    # Then
    assert result == {
        "allow_client_traits": True,
        "api_key": expected_api_key,
        "feature_states": [
            {
                "django_id": feature_state.pk,
                "enabled": False,
                "feature": {
                    "id": feature_state.feature.pk,
                    "name": "Test Feature1",
                    "type": "STANDARD",
                },
                "feature_segment": None,
                "feature_state_value": None,
                "featurestate_uuid": feature_state.uuid,
                "multivariate_feature_state_values": [],
            }
        ],
        "identity_overrides": [
            {
                "composite_key": identity.composite_key,
                "created_date": identity.created_date,
                "django_id": identity.pk,
                "environment_api_key": expected_api_key,
                "identifier": identity.identifier,
                "identity_features": [
                    {
                        "django_id": identity_featurestate.pk,
                        "enabled": True,
                        "feature": {
                            "id": identity_featurestate.feature.pk,
                            "name": identity_featurestate.feature.name,
                            "type": identity_featurestate.feature.type,
                        },
                        "feature_segment": None,
                        "feature_state_value": expected_overridden_value,
                        "featurestate_uuid": identity_featurestate.uuid,
                        "multivariate_feature_state_values": [],
                    }
                ],
                "identity_traits": [],
                "identity_uuid": mocker.ANY,
            }
        ],
        "hide_disabled_flags": None,
        "hide_sensitive_data": False,
        "id": environment.pk,
        "name": "Test Environment",
        "project": {
            "enable_realtime_updates": False,
            "hide_disabled_flags": False,
            "id": environment.project.pk,
            "name": "Test Project",
            "organisation": {
                "feature_analytics": False,
                "id": environment.project.organisation.pk,
                "name": "Test Org",
                "persist_trait_data": True,
                "stop_serving_flags": False,
            },
            "segments": [],
            "server_key_only_feature_ids": [],
        },
        "updated_at": environment.updated_at,
        "use_identity_composite_key_for_hashing": True,
    }
