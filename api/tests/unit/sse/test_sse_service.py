from sse.sse_service import (
    send_environment_update_message_using_environment,
    send_environment_update_message_using_project,
    send_identity_update_message,
    send_identity_update_messages,
)


def test_send_environment_update_message_using_project_schedules_task_correctly(
    mocker,
    settings,
    realtime_enabled_project,
    realtime_enabled_project_environment_one,
    realtime_enabled_project_environment_two,
):
    # Given
    settings.SSE_SERVER_BASE_URL = "http://localhost:8000"
    settings.SSE_AUTHENTICATION_TOKEN = "test-token"
    mocked_tasks = mocker.patch("sse.sse_service.tasks")

    # When
    send_environment_update_message_using_project(realtime_enabled_project)

    # Then
    environment_keys = list(
        realtime_enabled_project.environments.all().values_list("api_key", flat=True)
    )
    mocked_tasks.send_environment_update_messages.delay.assert_called_once_with(
        args=(environment_keys,)
    )


def test_send_environment_update_message_using_environment_schedules_task_correctly(
    mocker, settings, realtime_enabled_project_environment_one
):
    # Given
    settings.SSE_SERVER_BASE_URL = "http://localhost:8000"
    settings.SSE_AUTHENTICATION_TOKEN = "test-token"
    mocked_tasks = mocker.patch("sse.sse_service.tasks")

    # When
    send_environment_update_message_using_environment(
        realtime_enabled_project_environment_one
    )

    # Then
    mocked_tasks.send_environment_update_messages.delay.assert_called_once_with(
        args=([realtime_enabled_project_environment_one.api_key],)
    )


def test_send_identity_update_message_schedules_task_correctly(
    mocker, settings, realtime_enabled_project_environment_one
):
    # Given
    settings.SSE_SERVER_BASE_URL = "http://localhost:8000"
    settings.SSE_AUTHENTICATION_TOKEN = "test-token"
    mocked_tasks = mocker.patch("sse.sse_service.tasks")

    # When
    send_identity_update_message(
        realtime_enabled_project_environment_one, "test-identity"
    )

    # Then
    mocked_tasks.send_identity_update_message.delay.assert_called_once_with(
        args=(realtime_enabled_project_environment_one.api_key, "test-identity")
    )


def test_send_identity_update_messages_schedules_task_correctly(
    mocker, settings, realtime_enabled_project_environment_one
):
    # Given
    settings.SSE_SERVER_BASE_URL = "http://localhost:8000"
    settings.SSE_AUTHENTICATION_TOKEN = "test-token"
    mocked_tasks = mocker.patch("sse.sse_service.tasks")

    # When
    send_identity_update_messages(
        realtime_enabled_project_environment_one, ["test-identity-1", "test-identity-2"]
    )

    # Then
    mocked_tasks.send_identity_update_messages.delay.assert_called_once_with(
        args=(
            realtime_enabled_project_environment_one.api_key,
            ["test-identity-1", "test-identity-2"],
        )
    )
