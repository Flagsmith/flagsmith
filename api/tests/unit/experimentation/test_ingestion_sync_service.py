from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from redis.exceptions import RedisError

from experimentation import ingestion_sync_service


def test_set_environment_key__valid_key__writes_to_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_environment_key("test-env-key-001")

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_keys:test-env-key-001",
        "",
    )


def test_delete_environment_key__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_environment_key("test-env-key-001")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_keys:test-env-key-001",
    )


def test_set_environment_key__redis_error__logs_and_swallows(
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.set.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_environment_key("test-env-key-001")

    # Then
    assert any(
        event["event"] == "ingestion_sync.environment_key.failed"
        and event["level"] == "error"
        for event in log.events
    )


def test_delete_environment_key__redis_error__logs_and_swallows(
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.delete.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_environment_key("test-env-key-001")

    # Then
    assert any(
        event["event"] == "ingestion_sync.environment_key.failed"
        and event["level"] == "error"
        for event in log.events
    )
