from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from experimentation import ingestion_redis


def test_get_client__configured_url__builds_redis_cluster_with_socket_options(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    mock_from_url = mocker.patch(
        "experimentation.ingestion_redis.RedisCluster.from_url",
    )
    ingestion_redis.get_client.cache_clear()

    # When
    client = ingestion_redis.get_client()

    # Then
    mock_from_url.assert_called_once_with(
        "redis://ingestion:6379",
        socket_timeout=ingestion_redis.SOCKET_TIMEOUT,
        socket_keepalive=True,
    )
    assert client is mock_from_url.return_value
    ingestion_redis.get_client.cache_clear()
