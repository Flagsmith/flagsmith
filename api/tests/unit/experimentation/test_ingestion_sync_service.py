from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from pytest_mock import MockerFixture
from redis.exceptions import RedisError

from experimentation import ingestion_sync_service


def test_get_client__configured_url__builds_redis_cluster_with_socket_options(
    mocker: MockerFixture,
    settings: object,
) -> None:
    # Given
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"  # type: ignore[attr-defined]
    mock_from_url = mocker.patch(
        "experimentation.ingestion_sync_service.RedisCluster.from_url",
    )

    # When
    client = ingestion_sync_service._get_client()

    # Then
    mock_from_url.assert_called_once_with(
        "redis://ingestion:6379",
        socket_timeout=ingestion_sync_service.SOCKET_TIMEOUT,
        socket_keepalive=True,
    )
    assert client is mock_from_url.return_value


def test_set_ingestion_key__no_expiry__writes_environment_key_without_ttl(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
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
        "experimentation.ingestion_sync_service._get_client",
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
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_key("ser.test-key-001")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
    )


def test_set_ingestion_destination__valid_stream__writes_stream_name(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_destination(
        "client-env-key",
        stream_name="events-ingestion-org-1",
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_destinations:client-env-key",
        "events-ingestion-org-1",
    )


def test_delete_ingestion_destination__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
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
        "experimentation.ingestion_sync_service._get_client",
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
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When / Then
    with pytest.raises(RedisError, match="boom"):
        ingestion_sync_service.delete_ingestion_key("ser.test-key-001")
