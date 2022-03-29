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


def test_dynatrace_when_generate_event_data_with_correct_values_then_success():
    # Given
    log = "some log data"
    email = "tes@email.com"
    env = "test"
    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == env


def test_dynatrace_when_generate_event_data_with_with_missing_values_then_success():
    # Given no log or email data
    log = None
    email = None
    env = "test"
    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"
    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == env
