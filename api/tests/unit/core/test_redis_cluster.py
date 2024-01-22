import pytest
from core.redis_cluster import ClusterConnectionFactory
from django.core.exceptions import ImproperlyConfigured
from pytest_mock import MockerFixture


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
        decode_responses=True, host="localhost", port=6379
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
    with pytest.raises(ImproperlyConfigured):
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
