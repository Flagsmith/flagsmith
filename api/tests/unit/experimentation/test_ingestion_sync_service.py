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


def test_set_environment_key__redis_error__propagates(
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
        ingestion_sync_service.set_environment_key("test-env-key-001")


def test_delete_environment_key__redis_error__propagates(
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
        ingestion_sync_service.delete_environment_key("test-env-key-001")
