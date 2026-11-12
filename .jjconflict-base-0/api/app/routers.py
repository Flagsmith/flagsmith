from typing import Any, Literal, get_args

from common.core.utils import ReplicaNamePrefix
from django.db.models import Model

AnalyticsDatabaseName = Literal["analytics"]
ClickHouseDatabaseName = Literal["clickhouse"]

PRIMARY_DATABASE_NAME = "default"
REPLICA_NAME_PREFIXES: tuple[str, ...] = get_args(ReplicaNamePrefix)


class AnalyticsRouter:
    route_app_labels = ["app_analytics"]

    def db_for_read(
        self, model: type[Model], **hints: Any
    ) -> AnalyticsDatabaseName | None:
        """Route read queries to the 'analytics' database"""
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def db_for_write(
        self, model: type[Model], **hints: Any
    ) -> AnalyticsDatabaseName | None:
        """Route write queries to the 'analytics' database"""
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def allow_relation(self, obj1: Model, obj2: Model, **hints: Any) -> bool | None:
        """Allow relations between analytics models"""
        if (
            obj1._meta.app_label in self.route_app_labels
            and obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db: str, app_label: str, **hints: Any) -> bool | None:
        """Ensure the analytics database only gets analytics models"""
        if db == "analytics":
            return app_label in self.route_app_labels
        return None


class ClickHouseRouter:
    route_app_labels = ["clickhouse"]

    def db_for_read(
        self, model: type[Model], **hints: Any
    ) -> ClickHouseDatabaseName | None:
        if model._meta.app_label in self.route_app_labels:
            return "clickhouse"
        return None

    def db_for_write(
        self, model: type[Model], **hints: Any
    ) -> ClickHouseDatabaseName | None:
        if model._meta.app_label in self.route_app_labels:
            return "clickhouse"
        return None

    def allow_relation(self, obj1: Model, obj2: Model, **hints: Any) -> bool | None:
        # ClickHouse has no FKs and we don't expose CH-app models, so any
        # relation involving this app is forbidden.
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return False
        return None

    def allow_migrate(self, db: str, app_label: str, **hints: Any) -> bool | None:
        if db == "clickhouse":
            return app_label in self.route_app_labels
        if app_label in self.route_app_labels:
            return False
        return None


class ReplicaRouter:
    """
    Treat the primary database and its read replicas as one logical database.

    Replicas hold copies of the primary's data, so an object read from a replica
    can legitimately be related to an object read from the primary.

    Only `allow_relation` is implemented.

    This router must be registered last so that the restrictions of other routers
    keep taking precedence.
    """

    def allow_relation(self, obj1: Model, obj2: Model, **hints: Any) -> bool | None:
        databases = (obj1._state.db, obj2._state.db)
        if all(
            database is not None
            and (
                database == PRIMARY_DATABASE_NAME
                or database.startswith(REPLICA_NAME_PREFIXES)
            )
            for database in databases
        ):
            return True
        # Defer to the remaining routers for anything
        # that isn't the primary or one of its replicas.
        return None
