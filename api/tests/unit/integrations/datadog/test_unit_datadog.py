import json

import pytest
from pytest_mock import MockerFixture

from audit.models import AuditLog
from environments.models import Environment
from integrations.common.models import IntegrationHealthRecord
from integrations.datadog.datadog import (
    EVENTS_API_URI,
    FLAGSMITH_SOURCE_TYPE_NAME,
    DataDogWrapper,
)
from integrations.datadog.models import DataDogConfiguration


@pytest.mark.parametrize(
    "base_url, expected_events_url",
    (
        ("https://test.com", f"https://test.com/{EVENTS_API_URI}"),
        ("https://test.com/", f"https://test.com/{EVENTS_API_URI}"),
    ),
)
def test_datadog_init__valid_base_url__sets_correct_events_url(  # type: ignore[no-untyped-def]
    base_url, expected_events_url
):
    # Given
    api_key = "123key"

    # When initialized
    data_dog = DataDogWrapper(
        DataDogConfiguration(
            api_key=api_key,
            base_url=base_url,
            use_custom_source=True,
        )
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
@pytest.mark.django_db
def test_datadog_track_event__given_event_data__posts_expected_data(
    mocker: MockerFixture,
    event_data: dict,  # type: ignore[type-arg]
    use_custom_source: bool,
    expected_data: dict,  # type: ignore[type-arg]
) -> None:
    # Given
    base_url = "https://test.com"
    api_key = "key"
    mock_session = mocker.MagicMock()
    mock_session.post.return_value.status_code = 200
    record_integration_health_mock = mocker.patch(
        "integrations.datadog.datadog.record_integration_health",
        autospec=True,
    )

    datadog = DataDogWrapper(
        DataDogConfiguration(
            api_key=api_key,
            base_url=base_url,
            use_custom_source=use_custom_source,
        ),
        session=mock_session,
    )

    # When
    datadog._track_event(event_data)

    # Then
    mock_session.post.assert_called_once_with(
        f"{datadog.events_url}?api_key={api_key}", data=json.dumps(expected_data)
    )
    record_integration_health_mock.assert_called_once_with(datadog.config, 200)


def test_generate_event_data__valid_audit_log__returns_correct_event(  # type: ignore[no-untyped-def]
    django_user_model,
    feature,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    data_dog = DataDogWrapper(
        DataDogConfiguration(api_key="123key", base_url="http://test.com")
    )

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{environment.name}"


def test_generate_event_data__missing_author__returns_system_user(feature):  # type: ignore[no-untyped-def]
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    data_dog = DataDogWrapper(
        DataDogConfiguration(api_key="123key", base_url="http://test.com")
    )

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == f"env:{environment.name}"


def test_generate_event_data__missing_environment__returns_unknown_env(  # type: ignore[no-untyped-def]
    django_user_model,
    feature,
):
    # Given environment
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(log=log, author=author)

    data_dog = DataDogWrapper(
        DataDogConfiguration(api_key="123key", base_url="http://test.com")
    )

    # When
    event_data = data_dog.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"
    assert event_data["text"] == expected_event_text
    assert len(event_data["tags"]) == 1
    assert event_data["tags"][0] == "env:unknown"


@pytest.mark.django_db
def test_datadog_track_event__records_health_status(
    mocker: MockerFixture,
    project,
) -> None:
    # Given
    config = DataDogConfiguration.objects.create(
        project=project,
        api_key="123key",
        base_url="https://test.com",
    )
    mock_session = mocker.MagicMock()
    mock_session.post.return_value.status_code = 200
    datadog = DataDogWrapper(config, session=mock_session)

    # When
    datadog._track_event({"foo": "bar"})

    # Then
    health_record = IntegrationHealthRecord.objects.get(object_id=config.id)
    assert health_record.status_code == 200
