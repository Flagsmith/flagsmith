from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from pytest_mock import MockerFixture
from redis.exceptions import RedisError

from experimentation import ingestion_sync_service


def test_set_ingestion_key__no_expiry__writes_environment_key_without_ttl(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_key(
        "ser.test-key-001",
        environment_key="client-env-key",
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
        "client-env-key",
        exat=None,
    )


def test_set_ingestion_key__expiry__writes_environment_key_with_ttl(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )
    expires_at = datetime(2026, 9, 1, tzinfo=dt_timezone.utc)

    # When
    ingestion_sync_service.set_ingestion_key(
        "ser.test-key-001",
        environment_key="client-env-key",
        expires_at=expires_at,
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
        "client-env-key",
        exat=int(expires_at.timestamp()),
    )


def test_delete_ingestion_key__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_key("ser.test-key-001")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
    )


def test_set_ingestion_destination__valid_topic__writes_topic(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_destination(
        "client-env-key",
        topic="external_warehouse_events",
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_destinations:client-env-key",
        "external_warehouse_events",
    )


def test_delete_ingestion_destination__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_destination("client-env-key")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_destinations:client-env-key",
    )


def test_set_ingestion_key__redis_error__propagates(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.set.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When / Then
    with pytest.raises(RedisError, match="boom"):
        ingestion_sync_service.set_ingestion_key(
            "ser.test-key-001",
            environment_key="client-env-key",
        )


def test_delete_ingestion_key__redis_error__propagates(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.delete.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service.get_client",
        return_value=mock_client,
    )

    # When / Then
    with pytest.raises(RedisError, match="boom"):
        ingestion_sync_service.delete_ingestion_key("ser.test-key-001")
