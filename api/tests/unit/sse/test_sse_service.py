import boto3
import pytest
from django.conf import settings
from moto import mock_s3
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture

from sse.dataclasses import SSEAccessLogs
from sse.sse_service import (
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
    stream_access_logs,
)


def test_send_environment_update_message_for_project_schedules_task_correctly(
    mocker,
    sse_enabled_settings,
    realtime_enabled_project,
):
    # Given
    mocked_tasks = mocker.patch("sse.sse_service.tasks", autospec=True)

    # When
    send_environment_update_message_for_project(realtime_enabled_project)

    # Then
    mocked_tasks.send_environment_update_message_for_project.delay.assert_called_once_with(
        args=(realtime_enabled_project.id,)
    )


@pytest.mark.parametrize(
    "test_settings, test_project",
    [
        (
            lazy_fixture("sse_enabled_settings"),
            lazy_fixture("project"),
        ),
        (
            lazy_fixture("sse_disabled_settings"),
            lazy_fixture("realtime_enabled_project"),
        ),
    ],
)
def test_send_environment_update_message_for_project_exits_early_without_scheduling_task(
    mocker,
    test_settings,
    test_project,
):
    # Given
    mocked_tasks = mocker.patch("sse.sse_service.tasks", autospec=True)

    # When
    send_environment_update_message_for_project(test_project)

    # Then
    mocked_tasks.send_environment_update_message_for_project.delay.assert_not_called()


@pytest.mark.parametrize(
    "test_settings, test_environment ",
    [
        (
            lazy_fixture("sse_enabled_settings"),
            lazy_fixture("environment"),
        ),
        (
            lazy_fixture("sse_disabled_settings"),
            lazy_fixture("realtime_enabled_project_environment_one"),
        ),
    ],
)
def test_send_environment_update_message_for_environment_exits_early_without_scheduling_task(
    mocker, test_settings, test_environment
):
    # Given
    mocked_tasks = mocker.patch("sse.sse_service.tasks", autospec=True)

    # When
    send_environment_update_message_for_environment(test_environment)

    # Then
    mocked_tasks.send_environment_update_message.delay.assert_not_called()


def test_send_environment_update_message_for_environment_schedules_task_correctly(
    mocker, sse_enabled_settings, realtime_enabled_project_environment_one
):
    # Given
    mocked_tasks = mocker.patch("sse.sse_service.tasks", autospec=True)

    # When
    send_environment_update_message_for_environment(
        realtime_enabled_project_environment_one
    )

    # Then
    mocked_tasks.send_environment_update_message.delay.assert_called_once_with(
        args=(
            realtime_enabled_project_environment_one.api_key,
            realtime_enabled_project_environment_one.updated_at.isoformat(),
        )
    )


@mock_s3
def test_stream_access_logs(mocker: MockerFixture, aws_credentials: None) -> None:
    # Given - Some test data
    first_log = SSEAccessLogs("2023-11-27T06:42:47+0000", "key_one")
    second_log = SSEAccessLogs("2023-11-27T06:42:47+0000", "key_two")
    third_log = SSEAccessLogs("2023-11-27T06:42:47+0000", "key_three")

    first_encrypted_object_data = b"first_bucket_encrypted_data"
    first_decrypted_object_data = (
        f"{first_log.generated_at},{first_log.api_key}\n"
        f"{second_log.generated_at},{second_log.api_key}\n"
        "some,invalid,log,entry,111,222".encode()
    )
    second_encrypted_object_data = b"second_bucket_encrypted_data"
    second_decrypted_object_data = (
        f"{third_log.generated_at},{third_log.api_key}".encode()
    )

    # Next, let's create a bucket
    bucket_name = settings.AWS_SSE_LOGS_BUCKET_NAME
    s3_client = boto3.client("s3", region_name="eu-west-2")
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    # put some objects
    s3_client.put_object(
        Body=first_encrypted_object_data, Bucket=bucket_name, Key="first_object"
    )
    s3_client.put_object(
        Body=second_encrypted_object_data, Bucket=bucket_name, Key="second_object"
    )

    mocked_gpg = mocker.patch("sse.sse_service.gnupg.GPG", autospec=True)

    mocked_gpg.return_value.decrypt.side_effect = [
        mocker.MagicMock(data=first_decrypted_object_data),
        mocker.MagicMock(data=second_decrypted_object_data),
    ]

    # When
    access_logs = list(stream_access_logs())

    # Then
    assert access_logs == [first_log, second_log, third_log]

    # gpg decrypt was called correctly
    mocked_gpg.return_value.decrypt.assert_has_calls(
        [
            mocker.call(first_encrypted_object_data),
            mocker.call(second_encrypted_object_data),
        ]
    )

    # And, bucket is now empty
    assert "Contents" not in s3_client.list_objects(Bucket=bucket_name)
