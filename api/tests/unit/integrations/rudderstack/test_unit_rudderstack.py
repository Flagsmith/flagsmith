import typing

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.rudderstack.rudderstack import RudderstackWrapper


def test_rudderstack_generate_user_data__valid_identity__returns_expected_data(  # type: ignore[no-untyped-def]
    environment: Environment,
    feature: Feature,
):
    # Given
    rudderstack_config = RudderstackConfiguration(
        api_key="123key", base_url="https://api.rudderstack.com/"
    )
    rudderstack_wrapper = RudderstackWrapper(rudderstack_config)
    identity = Identity.objects.create(identifier="user123", environment=environment)
    feature_states = FeatureState.objects.filter(feature=feature)

    # When
    user_data = rudderstack_wrapper.generate_user_data(
        identity=identity, feature_states=feature_states
    )

    # Then
    assert user_data == {
        "user_id": identity.identifier,
        "traits": {feature.name: False},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "feature_state_with_value,expected_property_value",
    [(False, False), (True, True), ("foo", "foo"), (1, 1), (0, 0), ("", ""), (None, True)],
    indirect=["feature_state_with_value"],
)
def test_rudderstack_generate_user_data__falsy_values__returns_value_not_enabled_state(
    expected_property_value: typing.Any,
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
) -> None:
    # Given
    config = RudderstackConfiguration(
        api_key="123key", base_url="https://api.rudderstack.com/"
    )
    rudderstack_wrapper = RudderstackWrapper(config)

    # When
    user_data = rudderstack_wrapper.generate_user_data(
        identity=identity,
        feature_states=[feature_state, feature_state_with_value],
    )

    # Then
    assert user_data == {
        "user_id": identity.identifier,
        "traits": {
            feature_state.feature.name: feature_state.enabled,
            feature_state_with_value.feature.name: expected_property_value,
        },
    }
