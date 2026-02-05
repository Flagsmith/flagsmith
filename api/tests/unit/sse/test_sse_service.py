import boto3
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from moto import mock_s3  # type: ignore[import-untyped]
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from sse.dataclasses import SSEAccessLogs
from sse.sse_service import (
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
    stream_access_logs,
)


def test_send_environment_update_message_for_project_schedules_task_correctly(  # type: ignore[no-untyped-def]
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
def test_send_environment_update_message_for_project_exits_early_without_scheduling_task(  # type: ignore[no-untyped-def]  # noqa: E501
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
def test_send_environment_update_message_for_environment_exits_early_without_scheduling_task(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, test_settings, test_environment
):
    # Given
    mocked_tasks = mocker.patch("sse.sse_service.tasks", autospec=True)

    # When
    send_environment_update_message_for_environment(test_environment)

    # Then
    mocked_tasks.send_environment_update_message.delay.assert_not_called()


def test_send_environment_update_message_for_environment_schedules_task_correctly(  # type: ignore[no-untyped-def]
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


@mock_s3  # type: ignore[misc]
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
    assert bucket_name
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


def test_stream_access_logs_handles_deleted_files(
    mocker: MockerFixture, aws_credentials: None
) -> None:
    # Given - Mock bucket with objects where first raises NoSuchKey
    mock_obj_1 = mocker.MagicMock()
    mock_obj_1.key = "file1"
    mock_obj_1.get.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey"}}, "GetObject"
    )

    mock_obj_2 = mocker.MagicMock()
    mock_obj_2.key = "file2"
    mock_obj_2.get.return_value = {"Body": mocker.MagicMock(read=lambda: b"data2")}

    mock_bucket = mocker.MagicMock()
    mock_bucket.objects.all.return_value = [mock_obj_1, mock_obj_2]

    mocker.patch(
        "sse.sse_service.boto3.resource"
    ).return_value.Bucket.return_value = mock_bucket
    mocker.patch(
        "sse.sse_service.gnupg.GPG"
    ).return_value.decrypt.return_value = mocker.MagicMock(
        data=b"2023-11-27T06:42:47+0000,test_key"
    )
    mocked_logger = mocker.patch("sse.sse_service.logger")

    # When
    logs = list(stream_access_logs())

    # Then - Should skip first file with warning and process second
    assert len(logs) == 1
    mocked_logger.warning.assert_called_once_with(
        "Log file %s has already been deleted, skipping", "file1"
    )


def test_stream_access_logs_reraises_non_nosuchkey_errors(
    mocker: MockerFixture, aws_credentials: None
) -> None:
    # Given - Mock bucket with object that raises AccessDenied error
    mock_obj = mocker.MagicMock()
    mock_obj.key = "file1"
    mock_obj.get.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "GetObject"
    )

    mock_bucket = mocker.MagicMock()
    mock_bucket.objects.all.return_value = [mock_obj]

    mocker.patch(
        "sse.sse_service.boto3.resource"
    ).return_value.Bucket.return_value = mock_bucket
    mocker.patch("sse.sse_service.gnupg.GPG")

    # When/Then - Should re-raise the ClientError
    with pytest.raises(ClientError) as exc_info:
        list(stream_access_logs())

    assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


def test_stream_access_logs_respects_timeout(
    mocker: MockerFixture, aws_credentials: None
) -> None:
    # Given - Mock bucket with multiple objects
    mock_obj_1 = mocker.MagicMock()
    mock_obj_1.key = "file1"
    mock_obj_1.get.return_value = {"Body": mocker.MagicMock(read=lambda: b"data1")}

    mock_obj_2 = mocker.MagicMock()
    mock_obj_2.key = "file2"
    mock_obj_2.get.return_value = {"Body": mocker.MagicMock(read=lambda: b"data2")}

    mock_obj_3 = mocker.MagicMock()
    mock_obj_3.key = "file3"
    mock_obj_3.get.return_value = {"Body": mocker.MagicMock(read=lambda: b"data3")}

    mock_bucket = mocker.MagicMock()
    mock_bucket.objects.all.return_value = [mock_obj_1, mock_obj_2, mock_obj_3]

    mocker.patch(
        "sse.sse_service.boto3.resource"
    ).return_value.Bucket.return_value = mock_bucket

    # Mock GPG to return valid log data
    mocker.patch(
        "sse.sse_service.gnupg.GPG"
    ).return_value.decrypt.return_value = mocker.MagicMock(
        data=b"2023-11-27T06:42:47+0000,test_key"
    )

    # Mock time.time() to simulate timeout after processing first file
    mock_time = mocker.patch("sse.sse_service.time.time")
    mock_time.side_effect = [
        0,  # start_time
        0,  # first check (before file 1) - elapsed = 0
        10,  # second check (before file 2) - elapsed = 10 (exceeds timeout)
    ]

    mocked_logger = mocker.patch("sse.sse_service.logger")

    # When - Stream with a 5 second timeout
    logs = list(stream_access_logs(timeout_seconds=5))

    # Then - Should only process first file and stop at timeout
    assert len(logs) == 1
    mock_obj_1.delete.assert_called_once()
    mock_obj_2.delete.assert_not_called()
    mock_obj_3.delete.assert_not_called()

    mocked_logger.warning.assert_called_once_with(
        "stream_access_logs timeout reached after %.2f seconds, stopping log processing",
        10,
    )
