import typing

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.heap.heap import HeapWrapper
from integrations.heap.models import HeapConfiguration
from integrations.integration import identify_integrations

if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.django_db
@pytest.mark.parametrize(
    "feature_state_with_value,expected_property_value",
    [(False, False), (True, True), ("foo", "foo"), (1, 1), (0, 0)],
    indirect=["feature_state_with_value"],
)
def test_heap_generate_user_data__correct_values__returns_expected_data(
    expected_property_value: typing.Any,
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
) -> None:
    # Given
    api_key = "123key"
    config = HeapConfiguration(api_key=api_key)
    heap_wrapper = HeapWrapper(config)
    assert heap_wrapper.url == "https://heapanalytics.com/api/track"

    # When
    user_data = heap_wrapper.generate_user_data(
        identity=identity, feature_states=[feature_state, feature_state_with_value]
    )

    # Then
    expected_user_data = {
        "app_id": api_key,
        "identity": identity.identifier,
        "event": "Flagsmith Feature Flags",
        "properties": {
            feature_state.feature.name: feature_state.enabled,
            feature_state_with_value.feature.name: expected_property_value,
        },
    }
    assert expected_user_data == user_data


def test_heap_wrapper__eu_base_url__uses_eu_url() -> None:
    # Given
    config = HeapConfiguration(
        api_key="123key",
        base_url="https://eu.heapanalytics.com",
    )

    # When
    heap_wrapper = HeapWrapper(config)

    # Then
    assert heap_wrapper.url == "https://eu.heapanalytics.com/api/track"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "base_url, expected_url",
    [
        (None, "https://heapanalytics.com/api/track"),
        ("", "https://heapanalytics.com/api/track"),
        ("https://eu.heapanalytics.com", "https://eu.heapanalytics.com/api/track"),
        ("https://eu.heapanalytics.com/", "https://eu.heapanalytics.com/api/track"),
    ],
)
def test_identify_integrations__heap_configured__posts_to_expected_url(
    mocker: "MockerFixture",
    environment: Environment,
    identity: Identity,
    base_url: str | None,
    expected_url: str,
) -> None:
    # Given
    api_key = "abc-123"
    HeapConfiguration.objects.create(
        environment=environment,
        api_key=api_key,
        base_url=base_url,
    )
    mocked_post = mocker.patch("integrations.heap.heap.requests.post")

    # When
    identify_integrations(identity, identity.get_all_feature_states())  # type: ignore[no-untyped-call]

    # Then
    assert mocked_post.call_args.args[0] == expected_url
    assert mocked_post.call_args.kwargs["json"]["app_id"] == api_key
