import logging
import random
from enum import Enum

from django.conf import settings
from django.core.cache import cache
from django.db import connections

from .exceptions import ImproperlyConfiguredError

logger = logging.getLogger(__name__)

CONNECTION_CHECK_CACHE_TTL = 2


class ReplicaReadStrategy(Enum):
    DISTRIBUTED = "DISTRIBUTED"
    SEQUENTIAL = "SEQUENTIAL"


def connection_check(database: str) -> bool:
    try:
        conn = connections.create_connection(database)
        conn.connect()
        usable = conn.is_usable()
        if not usable:
            logger.warning(
                f"Unable to access database {database} during connection check"
            )
    except Exception:
        usable = False
        logger.error(
            "Encountered exception during connection",
            exc_info=True,
        )

    if usable:
        cache.set(
            f"db_connection_active.{database}", "online", CONNECTION_CHECK_CACHE_TTL
        )
    else:
        cache.set(
            f"db_connection_active.{database}", "offline", CONNECTION_CHECK_CACHE_TTL
        )

    return usable


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        if settings.NUM_DB_REPLICAS == 0:
            return "default"

        replicas = [f"replica_{i}" for i in range(1, settings.NUM_DB_REPLICAS + 1)]
        replica = self._get_replica(replicas)
        if replica:
            # This return is the most likely as replicas should be
            # online and properly functioning.
            return replica

        # Since no replicas are available, fall back to the cross
        # region replicas which have worse availability.
        cross_region_replicas = [
            f"cross_region_replica_{i}"
            for i in range(1, settings.NUM_CROSS_REGION_DB_REPLICAS + 1)
        ]

        cross_region_replica = self._get_replica(cross_region_replicas)
        if cross_region_replica:
            return cross_region_replica

        # No available replicas, so fallback to the default.
        logger.warning(
            "Unable to serve any available replicas, falling back to default database"
        )
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_set = {
            "default",
            *[f"replica_{i}" for i in range(1, settings.NUM_DB_REPLICAS + 1)],
            *[
                f"cross_region_replica_{i}"
                for i in range(1, settings.NUM_CROSS_REGION_DB_REPLICAS + 1)
            ],
        }
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"

    def _get_replica(self, replicas: list[str]) -> None | str:
        while replicas:
            if settings.REPLICA_READ_STRATEGY == ReplicaReadStrategy.DISTRIBUTED:
                database = random.choice(replicas)
            elif settings.REPLICA_READ_STRATEGY == ReplicaReadStrategy.SEQUENTIAL:
                database = replicas[0]
            else:
                raise ImproperlyConfiguredError(
                    f"Unknown REPLICA_READ_STRATEGY {settings.REPLICA_READ_STRATEGY}"
                )

            replicas.remove(database)
            db_cache = cache.get(f"db_connection_active.{database}")
            if db_cache == "online":
                return database
            if db_cache == "offline":
                continue

            if connection_check(database):
                return database


class AnalyticsRouter:
    route_app_labels = ["app_analytics"]

    def db_for_read(self, model, **hints):
        """
        Attempts to read analytics models go to 'analytics' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write analytics models go to 'analytics' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the analytics database.
        """
        if (
            obj1._meta.app_label in self.route_app_labels
            and obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the analytics app only appears in the 'analytics' database
        """
        if app_label in self.route_app_labels:
            if db != "default":
                return db == "analytics"
        return None
