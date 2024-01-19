from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.rudderstack.rudderstack import RudderstackWrapper


def test_rudderstack_wrapper_generate_user_data(
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
