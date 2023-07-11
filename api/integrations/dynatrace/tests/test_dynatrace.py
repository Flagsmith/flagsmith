from audit.models import AuditLog
from environments.models import Environment
from integrations.dynatrace.dynatrace import EVENTS_API_URI, DynatraceWrapper


def test_dynatrace_initialized_correctly():
    # Given
    api_key = "123key"
    base_url = "http://test.com"
    entity_selector = "type(APPLICATION),entityName(docs)"

    # When initialized
    dynatrace = DynatraceWrapper(
        base_url=base_url, api_key=api_key, entity_selector=entity_selector
    )

    # Then
    expected_url = f"{base_url}{EVENTS_API_URI}?api-token={api_key}"
    assert dynatrace.url == expected_url


def test_dynatrace_when_generate_event_data_with_correct_values_then_success(django_user_model):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(
        audit_log_record=audit_log_record
    )

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == environment.name


def test_dynatrace_when_generate_event_data_with_missing_author_then_success():
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(
        audit_log_record=audit_log_record
    )

    # Then
    expected_event_text = f"{log} by user system"
    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == environment.name


def test_dynatrace_when_generate_event_data_with_missing_environment_then_success(django_user_model):
    # Given
    log = "some log data"

    author = django_user_model(email="test@example.com")

    audit_log_record = AuditLog(log=log, author=author)

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(
        audit_log_record=audit_log_record
    )

    # Then
    expected_event_text = f"{log} by user {author.email}"
    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == "unknown"
