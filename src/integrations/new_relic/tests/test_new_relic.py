from integrations.new_relic.new_relic import NewRelicWrapper, EVENTS_API_URI


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


def test_new_relic_when_generate_event_data_with_correct_values_then_success():
    # Given
    log = "some log data"
    email = "tes@email.com"
    env = "test"
    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")
    assert event_deployment_data["revision"] == f"env:{env}"
    assert event_deployment_data["changelog"] == expected_event_text


def test_new_relic_when_generate_event_data_with_with_missing_values_then_success():
    # Given
    log = None
    email = None
    env = "test"
    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == f"env:{env}"
    assert event_deployment_data["changelog"] == expected_event_text


def test_new_dog_when_generate_event_data_with_with_missing_env_then_success():
    # Given environment
    log = "some log data"
    email = "tes@email.com"
    env = None
    new_relic = NewRelicWrapper(
        base_url="http://test.com", api_key="123key", app_id="123id"
    )

    # When
    event_data = new_relic.generate_event_data(
        log=log, email=email, environment_name=env
    )

    # Then
    expected_event_text = f"{log} by user {email}"

    assert event_data.get("deployment") is not None
    event_deployment_data = event_data.get("deployment")

    assert event_deployment_data["revision"] == f"env:{env}"
    assert event_deployment_data["changelog"] == expected_event_text
