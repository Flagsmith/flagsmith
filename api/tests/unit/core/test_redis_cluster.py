import pytest
from core.redis_cluster import ClusterConnectionFactory, SafeRedisClusterClient
from django_redis.exceptions import ConnectionInterrupted
from pytest_mock import MockerFixture
from redis.exceptions import RedisClusterException


def test_cluster_connection_factory__connect_cache(mocker: MockerFixture):
    # Given
    mock_get_connection = mocker.patch.object(
        ClusterConnectionFactory, "get_connection"
    )
    connection_factory = ClusterConnectionFactory(options={})

    url = "redis://localhost:6379"
    make_connection_params = mocker.patch.object(
        connection_factory,
        "make_connection_params",
        return_value={"url": url},
    )

    # When
    first_connection = connection_factory.connect(url)

    # Let's call it again
    second_connection = connection_factory.connect(url)

    # Then
    assert first_connection == mock_get_connection.return_value
    assert second_connection == mock_get_connection.return_value
    assert first_connection is second_connection

    # get_connection was only called once
    mock_get_connection.assert_called_once_with({"url": url})

    # make_connection_params was only called once
    make_connection_params.assert_called_once_with(url)


def test_cluster_connection_factory__get_connection_with_non_conflicting_params(
    mocker: MockerFixture,
):
    # Given
    mockRedisCluster = mocker.patch("core.redis_cluster.RedisCluster")
    connection_factory = ClusterConnectionFactory(
        options={"REDIS_CLIENT_KWARGS": {"decode_responses": False}}
    )
    connection_params = {"host": "localhost", "port": 6379}

    # When
    connection_factory.get_connection(connection_params)

    # Then
    mockRedisCluster.assert_called_once_with(
        decode_responses=False,
        host="localhost",
        port=6379,
        socket_keepalive=True,
        socket_timeout=0.2,
    )


def test_cluster_connection_factory__get_connection_with_conflicting_params(
    mocker: MockerFixture,
):
    # Given
    mockRedisCluster = mocker.patch("core.redis_cluster.RedisCluster")
    connection_factory = ClusterConnectionFactory(
        options={"REDIS_CLIENT_KWARGS": {"decode_responses": False}}
    )
    connection_params = {"decode_responses": True}

    # When
    with pytest.raises(ConnectionInterrupted):
        connection_factory.get_connection(connection_params)

    # Then - ImproperlyConfigured exception is raised
    mockRedisCluster.assert_not_called()


def test_disconnect(mocker: MockerFixture):
    # Given
    connection_factory = ClusterConnectionFactory({})
    mock_connection = mocker.MagicMock()
    mock_disconnect_connection_pools = mocker.MagicMock()
    mock_connection.disconnect_connection_pools = mock_disconnect_connection_pools

    # When
    connection_factory.disconnect(mock_connection)

    # Then
    mock_disconnect_connection_pools.assert_called_once()


def test_safe_redis_cluster__safe_methods_raise_connection_interrupted(
    mocker: MockerFixture, settings
):
    # Given
    # Internal client that will raise RedisClusterException on every call
    mocked_redis_cluster_client = mocker.MagicMock(side_effect=RedisClusterException)

    safe_redis_cluster_client = SafeRedisClusterClient("redis://test", {}, None)

    # Replace the internal client with the mocked one
    safe_redis_cluster_client.get_client = mocked_redis_cluster_client

    # Mock the backend as well
    safe_redis_cluster_client._backend = mocker.MagicMock()

    # When / Then
    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.get("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.set("key", "value")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.incr_version("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.delete("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.delete_pattern("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.delete_many(["key"])

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.clear()

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.get_many(["key"])

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.set_many({"key": "value"})

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.incr("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.has_key("key")

    with pytest.raises(ConnectionInterrupted):
        safe_redis_cluster_client.keys("key")
