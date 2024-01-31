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

DJANGO_REDIS_CONNECTION_FACTORY = "core.redis_cluster.ClusterConnectionFactory"
"""

import threading
from copy import deepcopy

from django.core.exceptions import ImproperlyConfigured
from django_redis.pool import ConnectionFactory
from redis.cluster import RedisCluster


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
        client_cls_kwargs = deepcopy(self.redis_client_cls_kwargs)
        # ... and smash 'em together (crashing if there's conflicts)...
        for key, value in connection_params.items():
            if key in client_cls_kwargs:
                raise ImproperlyConfigured(
                    f"Found '{key}' in both the connection and the client kwargs"
                )
            client_cls_kwargs[key] = value

        # ... and then build and return the client
        return RedisCluster(**client_cls_kwargs)

    def disconnect(self, connection: RedisCluster):
        connection.disconnect_connection_pools()
