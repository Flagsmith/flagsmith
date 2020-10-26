from unittest import mock, SkipTest

from integrations.datadog.datadog import DataDogWrapper
from pytest import fail


# TODO: look into using https://github.com/betamaxpy/betamax or https://github.com/getsentry/responses
@SkipTest
@mock.patch("integrations.datadog.datadog.requests")
def test_datadog_track_event(mock_requests):
    # TODO: implement me
    fail()


@SkipTest
def test_datadog_generate_event_data():
    # TODO: implement me
    fail()


def test_datadog_initialized_correctly():
    # Given
    api_key = '123key'
    base_url = "http://test.com"

    # When initialized
    data_dog = DataDogWrapper(base_url="http://test.com", api_key='123key')

    # Then
    expected_url = f"{base_url}api/v1/events?api_key={api_key}"
    assert data_dog.url == expected_url


def test_datatog_when_generate_event_data_with_correct_values_then_success():
    # Given
    log = "some log data"
    email = "tes@email.com"
    env = "test"
    data_dog = DataDogWrapper(base_url="http://test.com", api_key='123key')

    # When
    event_data = data_dog.generate_event_data(log=log,
                                              email=email,
                                              environment_name=env)

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data['text'] == expected_event_text
    assert len(event_data['tags']) == 1
    assert event_data['tags'][0] == "env:" + env


def test_datatog_when_generate_event_data_with_with_missing_values_then_success():
    # Given no log or email data
    log = None
    email = None
    env = "test"
    data_dog = DataDogWrapper(base_url="http://test.com", api_key='123key')

    # When
    event_data = data_dog.generate_event_data(log=log,
                                              email=email,
                                              environment_name=env)

    # Then
    expected_event_text = f"{log} by user {email}"
    assert event_data['text'] == expected_event_text
    assert len(event_data['tags']) == 1
    assert event_data['tags'][0] == f"env:{env}"


def test_datatog_when_generate_event_data_with_with_missing_env_then_success():
    # Given environment
    log = "some log data"
    email = "tes@email.com"
    env = None
    data_dog = DataDogWrapper(base_url="http://test.com", api_key='123key')

    # When
    event_data = data_dog.generate_event_data(log=log,
                                              email=email,
                                              environment_name=env)

    # Then
    expected_event_text = f"{log} by user {email}"
    assert event_data['text'] == expected_event_text
    assert len(event_data['tags']) == 1
    assert event_data['tags'][0] == f"env:{env}"
