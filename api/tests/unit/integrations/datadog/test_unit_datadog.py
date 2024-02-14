import json

import pytest
from pytest_mock import MockerFixture

from audit.models import AuditLog
from environments.models import Environment
from integrations.datadog.datadog import (
    EVENTS_API_URI,
    FLAGSMITH_SOURCE_TYPE_NAME,
    DataDogWrapper,
)


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
    data_dog = DataDogWrapper(
        base_url=base_url, api_key=api_key, use_custom_source=True
    )

    # Then
    assert data_dog.events_url == expected_events_url
    assert data_dog.use_custom_source is True


@pytest.mark.parametrize(
    "event_data, use_custom_source, expected_data",
    (
        ({"foo": "bar"}, False, {"foo": "bar"}),
        (
            {"foo": "bar"},
            True,
            {"foo": "bar", "source_type_name": FLAGSMITH_SOURCE_TYPE_NAME},
        ),
    ),
)
def test_datadog_track_event(
    mocker: MockerFixture,
    event_data: dict,
    use_custom_source: bool,
    expected_data: dict,
) -> None:
    # Given
    base_url = "https://test.com"
    api_key = "key"
    mock_session = mocker.MagicMock()

    datadog = DataDogWrapper(
        base_url=base_url,
        api_key=api_key,
        session=mock_session,
        use_custom_source=use_custom_source,
    )

    # When
    datadog._track_event(event_data)

    # Then
    mock_session.post.assert_called_once_with(
        f"{datadog.events_url}?api_key={api_key}", data=json.dumps(expected_data)
    )


def test_datadog_when_generate_event_data_with_correct_values_then_success(
    django_user_model,
    feature,
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


def test_datadog_when_generate_event_data_with_missing_author_then_success(feature):
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    data_dog = DataDogWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{environment.name}"


def test_datadog_when_generate_event_data_with_missing_env_then_success(
    django_user_model,
    feature,
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
    assert event_data["tags"][0] == "env:unknown"
