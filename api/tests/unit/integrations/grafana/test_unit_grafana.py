from audit.models import AuditLog
from environments.models import Environment
from integrations.grafana.grafana import ANNOTATIONS_API_URI, GrafanaWrapper


def test_grafana_initialized_correctly():
    # Given
    api_key = "123key"
    base_url = "http://test.com"

    # When initialized
    grafana = GrafanaWrapper(base_url=base_url, api_key=api_key)

    # Then
    expected_url = f"{base_url}{ANNOTATIONS_API_URI}"
    assert grafana.url == expected_url


def test_grafana_when_generate_event_data_with_correct_values_then_success(
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    grafana = GrafanaWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = grafana.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("time") is not None
    assert event_data.get("timeEnd") is not None
    assert event_data.get("text") == expected_event_text


def test_grafana_when_generate_event_data_with_missing_author_then_success():
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    grafana = GrafanaWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = grafana.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"

    assert event_data.get("time") is not None
    assert event_data.get("timeEnd") is not None
    assert event_data.get("text") == expected_event_text


def test_grafana_when_generate_event_data_with_missing_env_then_success(
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(log=log, author=author)

    grafana = GrafanaWrapper(base_url="http://test.com", api_key="123key")

    # When
    event_data = grafana.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data.get("time") is not None
    assert event_data.get("timeEnd") is not None
    assert event_data.get("text") == expected_event_text
