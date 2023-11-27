from datetime import datetime
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from sse.dataclasses import SSEAccessLogs
from sse.exceptions import SSEAuthTokenNotSet
from sse.tasks import (
    get_auth_header,
    send_environment_update_message,
    send_environment_update_message_for_project,
    update_sse_usage,
)


def test_send_environment_update_message_for_project_make_correct_request(
    mocker,
    settings,
    realtime_enabled_project,
    realtime_enabled_project_environment_one,
    realtime_enabled_project_environment_two,
):
    # Given
    base_url = "http://localhost:8000"
    token = "token"

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("sse.tasks.requests")

    # When
    send_environment_update_message_for_project(realtime_enabled_project.id)

    # Then
    mocked_requests.post.has_calls(
        mocker.call(
            f"{base_url}/sse/environments/{realtime_enabled_project_environment_one.api_key}/queue-change",
            headers={"Authorization": f"Token {token}"},
            json={
                "updated_at": realtime_enabled_project_environment_one.updated_at.isoformat()
            },
            timeout=2,
        ),
        mocker.call(
            f"{base_url}/sse/environments/{realtime_enabled_project_environment_two.api_key}/queue-change",
            headers={"Authorization": f"Token {token}"},
            json={
                "updated_at": realtime_enabled_project_environment_two.updated_at.isoformat()
            },
            timeout=2,
        ),
    )


def test_send_environment_update_message_make_correct_request(mocker, settings):
    # Given
    base_url = "http://localhost:8000"
    token = "token"
    environment_key = "test_environment"
    updated_at = datetime.now().isoformat()

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("sse.tasks.requests")

    # When
    send_environment_update_message(environment_key, updated_at)

    # Then
    mocked_requests.post.assert_called_once_with(
        f"{base_url}/sse/environments/{environment_key}/queue-change",
        headers={"Authorization": f"Token {token}"},
        json={"updated_at": updated_at},
        timeout=2,
    )


def test_auth_header_raises_exception_if_token_not_set(settings):
    # Given
    settings.SSE_AUTHENTICATION_TOKEN = None

    # When
    with pytest.raises(SSEAuthTokenNotSet):
        get_auth_header()


def test_track_sse_usage(mocker: MockerFixture, environment: Environment):
    # Given - two valid logs
    first_access_log = SSEAccessLogs(datetime.now().isoformat(), environment.api_key)
    second_access_log = SSEAccessLogs(datetime.now().isoformat(), environment.api_key)

    # one log with invalid api key
    third_access_log = SSEAccessLogs(datetime.now().isoformat(), "third_key")

    mocker.patch(
        "sse.sse_service.stream_access_logs",
        return_value=[first_access_log, second_access_log, third_access_log],
    )

    mocked_influx_db_client = mocker.patch("sse.tasks.influxdb_client")
    mocked_influx_point = mocker.patch("sse.tasks.Point")

    # When
    update_sse_usage()

    # Then
    write_method = (
        mocked_influx_db_client.write_api.return_value.__enter__.return_value.write
    )
    # two valid logs should be written to influxdb
    assert write_method.call_count == 2
    write_method.assert_has_calls(
        [
            call(
                bucket="sse_dev",
                record=mocked_influx_point().field().tag().tag().tag().time(),
            ),
            call(
                bucket="sse_dev",
                record=mocked_influx_point().field().tag().tag().tag().time(),
            ),
        ]
    )

    # Point was generated correctly
    mocked_influx_point.assert_has_calls(
        [
            call("sse_call"),
            call().field("request_count", 1),
            call().field().tag("organisation_id", environment.project.organisation_id),
            call().field().tag().tag("project_id", environment.project_id),
            call().field().tag().tag().tag("environment_id", environment.id),
            call().field().tag().tag().tag().time(first_access_log.generated_at),
            # Second log
            call("sse_call"),
            call().field("request_count", 1),
            call().field().tag("organisation_id", environment.project.organisation_id),
            call().field().tag().tag("project_id", environment.project_id),
            call().field().tag().tag().tag("environment_id", environment.id),
            call().field().tag().tag().tag().time(second_access_log.generated_at),
        ]
    )
