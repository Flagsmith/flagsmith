import pytest

from audit.models import AuditLog
from environments.models import Environment
from integrations.common.models import IntegrationHealthRecord
from integrations.new_relic.models import NewRelicConfiguration
from integrations.new_relic.new_relic import EVENTS_API_URI, NewRelicWrapper


def test_new_relic_wrapper__valid_config__initializes_correctly():  # type: ignore[no-untyped-def]
    # Given
    config = NewRelicConfiguration(
        api_key="123key",
        app_id="123id",
        base_url="http://test.com",
    )

    # When initialized
    new_relic = NewRelicWrapper(config)

    # Then
    expected_url = f"{config.base_url}/{EVENTS_API_URI}{config.app_id}/deployments.json"
    assert new_relic.url == expected_url


def test_new_relic_generate_event_data__correct_values__returns_expected(  # type: ignore[no-untyped-def]
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    new_relic = NewRelicWrapper(
        NewRelicConfiguration(
            api_key="123key",
            app_id="123id",
            base_url="http://test.com",
        )
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")
    assert event_deployment_data["revision"] == f"env:{environment.name}"  # type: ignore[index]
    assert event_deployment_data["changelog"] == expected_event_text  # type: ignore[index]


def test_new_relic_generate_event_data__missing_author__returns_system_user():  # type: ignore[no-untyped-def]
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    new_relic = NewRelicWrapper(
        NewRelicConfiguration(
            api_key="123key",
            app_id="123id",
            base_url="http://test.com",
        )
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == f"env:{environment.name}"  # type: ignore[index]
    assert event_deployment_data["changelog"] == expected_event_text  # type: ignore[index]


def test_new_relic_generate_event_data__missing_environment__returns_unknown_env(  # type: ignore[no-untyped-def]
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(log=log, author=author)

    new_relic = NewRelicWrapper(
        NewRelicConfiguration(
            api_key="123key",
            app_id="123id",
            base_url="http://test.com",
        )
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == "env:unknown"  # type: ignore[index]
    assert event_deployment_data["changelog"] == expected_event_text  # type: ignore[index]


@pytest.mark.django_db
def test_new_relic_track_event__records_health_status(  # type: ignore[no-untyped-def]
    mocker,
    project,
):
    # Given
    config = NewRelicConfiguration.objects.create(
        project=project,
        api_key="123key",
        app_id="123id",
        base_url="http://test.com",
    )
    new_relic = NewRelicWrapper(config)
    mocked_post = mocker.patch("integrations.new_relic.new_relic.requests.post")
    mocked_post.return_value.status_code = 200

    # When
    new_relic._track_event({"deployment": {}})

    # Then
    health_record = IntegrationHealthRecord.objects.get(object_id=config.id)
    assert health_record.status_code == 200
