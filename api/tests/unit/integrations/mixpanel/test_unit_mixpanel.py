from integrations.mixpanel.mixpanel import MIXPANEL_API_URL, MixpanelWrapper
from integrations.mixpanel.models import MixpanelConfiguration


def test_mixpanel_initialized_correctly():
    # Given
    config = MixpanelConfiguration(api_key="123key")

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    expected_url = f"{MIXPANEL_API_URL}/engage#profile-set"
    assert mixpanel.url == expected_url
    assert mixpanel.api_key == config.api_key


def test_mixpanel_generate_user_data(project, feature, identity):
    # Given
    config = MixpanelConfiguration(api_key="123key")
    feature_states = feature.feature_states.all()

    mixpanel = MixpanelWrapper(config)

    # When
    user_data = mixpanel.generate_user_data(
        identity=identity, feature_states=feature_states
    )

    # Then
    feature_properties = {}

    for feature_state in feature_states:
        value = feature_state.get_feature_state_value()
        feature_properties[feature_state.feature.name] = (
            value if (feature_state.enabled and value) else feature_state.enabled
        )

    expected_user_data = [
        {
            "$distinct_id": identity.identifier,
            "$token": config.api_key,
            "$set": feature_properties,
            "$ip": "0",
        }
    ]

    assert user_data == expected_user_data
