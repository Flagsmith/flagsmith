from logging import DEBUG
from typing import TYPE_CHECKING

import pytest

from integrations.mixpanel.constants import DEFAULT_MIXPANEL_API_URL
from integrations.mixpanel.mixpanel import MixpanelWrapper
from integrations.mixpanel.models import MixpanelConfiguration

if TYPE_CHECKING:
    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture

    from environments.identities.models import Identity
    from environments.models import Environment
    from features.models import Feature
    from projects.models import Project


def test_mixpanel_wrapper__valid_config__initializes_correctly() -> None:
    # Given
    config = MixpanelConfiguration(api_key="123key")

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    expected_url = f"{DEFAULT_MIXPANEL_API_URL}/engage#profile-set"
    assert mixpanel.url == expected_url
    assert mixpanel.api_key == config.api_key


def test_mixpanel_wrapper__eu_base_url__uses_eu_url() -> None:
    # Given
    config = MixpanelConfiguration(
        api_key="123key",
        base_url="https://api-eu.mixpanel.com",
    )

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    assert mixpanel.url == "https://api-eu.mixpanel.com/engage#profile-set"


def test_mixpanel_wrapper__in_base_url__uses_in_url() -> None:
    # Given
    config = MixpanelConfiguration(
        api_key="123key",
        base_url="https://api-in.mixpanel.com",
    )

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    assert mixpanel.url == "https://api-in.mixpanel.com/engage#profile-set"


def test_mixpanel_wrapper__base_url_with_trailing_slash__strips_slash() -> None:
    # Given
    config = MixpanelConfiguration(
        api_key="123key",
        base_url="https://api-eu.mixpanel.com/",
    )

    # When
    mixpanel = MixpanelWrapper(config)

    # Then
    assert mixpanel.url == "https://api-eu.mixpanel.com/engage#profile-set"


def test_mixpanel_identify_user__valid_identity__posts_to_api(
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


def test_mixpanel_generate_user_data__identity_with_features__returns_expected_format(
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "base_url, expected_url",
    [
        (None, "https://api.mixpanel.com/engage#profile-set"),
        ("", "https://api.mixpanel.com/engage#profile-set"),
        (
            "https://api-eu.mixpanel.com",
            "https://api-eu.mixpanel.com/engage#profile-set",
        ),
        (
            "https://api-eu.mixpanel.com/",
            "https://api-eu.mixpanel.com/engage#profile-set",
        ),
        (
            "https://api-in.mixpanel.com",
            "https://api-in.mixpanel.com/engage#profile-set",
        ),
    ],
)
def test_identify_integrations__mixpanel_configured__posts_to_expected_url(
    mocker: "MockerFixture",
    environment: "Environment",
    identity: "Identity",
    base_url: str | None,
    expected_url: str,
) -> None:
    # Given
    from integrations.integration import identify_integrations

    api_key = "abc-123"
    MixpanelConfiguration.objects.create(
        environment=environment,
        api_key=api_key,
        base_url=base_url,
    )
    mocked_post = mocker.patch("integrations.mixpanel.mixpanel.requests.post")

    # When
    identify_integrations(identity, identity.get_all_feature_states())  # type: ignore[no-untyped-call]

    # Then
    assert mocked_post.call_args.args[0] == expected_url
    assert mocked_post.call_args.kwargs["json"][0]["$token"] == api_key
