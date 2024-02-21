"""
Temporary module that adds support for Redis Cluster to django-redis by implementing
a connection factory class(`ClusterConnectionFactory`).
This module should be removed once [this](https://github.com/jazzband/django-redis/issues/606)
is resolved.

Usage:
------
Include the following configuration in Django project's settings.py file:

```python
# settings.py

"cache_name: {
        "BACKEND": ...,
        "LOCATION": ...,
        "OPTIONS": {
            "CLIENT_CLASS": "core.redis_cluster.SafeRedisClusterClient",

        },
    },
"""

import threading
from copy import deepcopy

from django.core.exceptions import ImproperlyConfigured
from django_redis.client.default import DefaultClient
from django_redis.exceptions import ConnectionInterrupted
from django_redis.pool import ConnectionFactory
from redis.cluster import RedisCluster
from redis.exceptions import RedisClusterException

SOCKET_TIMEOUT = 0.2


class SafeRedisClusterClient(DefaultClient):
    SAFE_METHODS = [
        "set",
        "get",
        "incr_version",
        "delete",
        "delete_pattern",
        "delete_many",
        "clear",
        "get_many",
        "set_many",
        "incr",
        "has_key",
        "keys",
    ]

    @staticmethod
    def _safe_operation(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RedisClusterException as e:
                raise ConnectionInterrupted(connection=None) from e

        return wrapper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically generate safe versions of methods
        for method_name in self.SAFE_METHODS:
            setattr(
                self, method_name, self._safe_operation(getattr(super(), method_name))
            )

        # Let's use our own connection factory here
        self.connection_factory = ClusterConnectionFactory(options=self._options)


class ClusterConnectionFactory(ConnectionFactory):
    """A connection factory for redis.cluster.RedisCluster
    The cluster client manages connection pools internally, so we don't want to
    do it at this level like the base ConnectionFactory does.
    """

    # A global cache of URL->client so that within a process, we will reuse a
    # single client, and therefore a single set of connection pools.
    _clients = {}
    _clients_lock = threading.Lock()

    def connect(self, url: str) -> RedisCluster:
        """Given a connection url, return a client instance.
        Prefer to return from our cache but if we don't yet have one build it
        to populate the cache.
        """
        if url not in self._clients:
            with self._clients_lock:
                if url not in self._clients:
                    params = self.make_connection_params(url)
                    self._clients[url] = self.get_connection(params)

        return self._clients[url]

    def get_connection(self, connection_params: dict) -> RedisCluster:
        """
        Given connection_params, return a new client instance.
        Basic django-redis ConnectionFactory manages a cache of connection
        pools and builds a fresh client each time. because the cluster client
        manages its own connection pools, we will instead merge the
        "connection" and "client" kwargs and throw them all at the client to
        sort out.
        If we find conflicting client and connection kwargs, we'll raise an
        error.
        """
        try:
            client_cls_kwargs = deepcopy(self.redis_client_cls_kwargs)
            # ... and smash 'em together (crashing if there's conflicts)...
            for key, value in connection_params.items():
                if key in client_cls_kwargs:
                    raise ImproperlyConfigured(
                        f"Found '{key}' in both the connection and the client kwargs"
                    )
                client_cls_kwargs[key] = value

            # Add explicit socket timeout
            client_cls_kwargs["socket_timeout"] = SOCKET_TIMEOUT
            client_cls_kwargs["socket_keepalive"] = True
            # ... and then build and return the client
            return RedisCluster(**client_cls_kwargs)
        except Exception as e:
            # Let django redis handle the exception
            raise ConnectionInterrupted(connection=None) from e

    def disconnect(self, connection: RedisCluster):
        connection.disconnect_connection_pools()
