from logging import DEBUG
from typing import TYPE_CHECKING

from integrations.mixpanel.mixpanel import MIXPANEL_API_URL, MixpanelWrapper
from integrations.mixpanel.models import MixpanelConfiguration

if TYPE_CHECKING:
    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture

    from environments.identities.models import Identity
    from features.models import Feature
    from projects.models import Project


def test_mixpanel_initialized_correctly() -> None:
    # Given
    config = MixpanelConfiguration(api_key="123key")

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    expected_url = f"{MIXPANEL_API_URL}/engage#profile-set"
    assert mixpanel.url == expected_url
    assert mixpanel.api_key == config.api_key


def test_mixpanel_identity_user__calls_expected(
    mocker: "MockerFixture",
    caplog: "LogCaptureFixture",
    feature: "Feature",
    identity: "Identity",
) -> None:
    # Given
    caplog.set_level(DEBUG)
    config = MixpanelConfiguration(api_key="123key")
    feature_states = [*feature.feature_states.all()]

    mixpanel = MixpanelWrapper(config)
    expected_user_data = mixpanel.generate_user_data(
        identity=identity,
        feature_states=feature_states,
        trait_models=[],
    )
    post_mock = mocker.patch("integrations.mixpanel.mixpanel.requests.post")
    post_mock.return_value.status_code = 200
    post_mock.return_value.text = expected_response_text = "test content"

    # When
    mixpanel._identify_user(expected_user_data)

    # Then
    post_mock.assert_called_once_with(
        "https://api.mixpanel.com/engage#profile-set",
        headers={"Accept": "text/plain", "X-Mixpanel-Integration-ID": "flagsmith"},
        json=expected_user_data,
    )
    assert caplog.record_tuples == [
        (
            "integrations.mixpanel.mixpanel",
            DEBUG,
            "Sent event to Mixpanel. Response code was: 200",
        ),
        (
            "integrations.mixpanel.mixpanel",
            DEBUG,
            f"Sent event to Mixpanel. Response content was: {expected_response_text}",
        ),
    ]


def test_mixpanel_generate_user_data(
    project: "Project",
    feature: "Feature",
    identity: "Identity",
) -> None:
    # Given
    config = MixpanelConfiguration(api_key="123key")
    feature_states = [*feature.feature_states.all()]

    mixpanel = MixpanelWrapper(config)

    # When
    user_data = mixpanel.generate_user_data(
        identity=identity,
        feature_states=feature_states,
        trait_models=[],
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
