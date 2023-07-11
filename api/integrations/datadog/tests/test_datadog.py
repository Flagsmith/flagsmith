import json

import pytest

from audit.models import AuditLog
from environments.models import Environment
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


def test_datadog_when_generate_event_data_with_correct_values_then_success(
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{environment.name}"


def test_datadog_when_generate_event_data_with_missing_author_then_success():
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(
        audit_log_record=audit_log_record
    )

    # Then
    expected_event_text = f"{log} by user system"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{environment.name}"


def test_datadog_when_generate_event_data_with_missing_env_then_success(
    django_user_model,
):
    # Given environment
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(log=log, author=author)

    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:unknown"
