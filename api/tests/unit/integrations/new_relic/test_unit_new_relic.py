from audit.models import AuditLog
from environments.models import Environment
from integrations.new_relic.new_relic import EVENTS_API_URI, NewRelicWrapper


def test_new_relic_initialized_correctly():
    # Given
    api_key = "123key"
    app_id = "123id"
    base_url = "http://test.com"

    # When initialized
    new_relic = NewRelicWrapper(base_url=base_url, api_key=api_key, app_id=app_id)

    # Then
    expected_url = f"{base_url}{EVENTS_API_URI}{app_id}/deployments.json"
    assert new_relic.url == expected_url


def test_new_relic_when_generate_event_data_with_correct_values_then_success(
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")
    assert event_deployment_data["revision"] == f"env:{environment.name}"
    assert event_deployment_data["changelog"] == expected_event_text


def test_new_relic_when_generate_event_data_with_missing_author_then_success():
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == f"env:{environment.name}"
    assert event_deployment_data["changelog"] == expected_event_text


def test_new_relic_when_generate_event_data_with_missing_env_then_success(
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(log=log, author=author)

    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == "env:unknown"
    assert event_deployment_data["changelog"] == expected_event_text
