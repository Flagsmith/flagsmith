import json

import pytest

from integrations.datadog.datadog import EVENTS_API_URI, DataDogWrapper


@pytest.mark.parametrize(
    "base_url, expected_events_url",
    (
        ("https://test.com", f"https://test.com/{EVENTS_API_URI}"),
        ("https://test.com/", f"https://test.com/{EVENTS_API_URI}"),
    ),
)
def test_datadog_initialized_correctly(base_url, expected_events_url):
    # Given
    api_key = "123key"

    # When initialized
    data_dog = DataDogWrapper(base_url=base_url, api_key=api_key)

    # Then
    assert data_dog.events_url == expected_events_url


def test_datadog_track_event(mocker):
    # Given
    base_url = "https://test.com"
    api_key = "key"
    mock_session = mocker.MagicMock()

    datadog = DataDogWrapper(base_url=base_url, api_key=api_key, session=mock_session)

    event = {"foo": "bar"}

    # When
    datadog._track_event(event)

    # Then
    mock_session.post.assert_called_once_with(
        f"{datadog.events_url}?api_key={api_key}", data=json.dumps(event)
    )


def test_datadog_when_generate_event_data_with_correct_values_then_success():
    # Given
    log = "some log data"
    email = "tes@email.com"
    env = "test"
    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == "env:" + env


def test_datadog_when_generate_event_data_with_with_missing_values_then_success():
    # Given no log or email data
    log = None
    email = None
    env = "test"
    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{env}"


def test_datadog_when_generate_event_data_with_with_missing_env_then_success():
    # Given environment
    log = "some log data"
    email = "tes@email.com"
    env = None
    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{env}"
