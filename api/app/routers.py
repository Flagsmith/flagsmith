import random

from django.conf import settings


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        if settings.NUM_DB_REPLICAS == 0:
            return "default"
        return random.choice(
            [f"replica_{i}" for i in range(1, settings.NUM_DB_REPLICAS + 1)]
        )

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
        }
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"


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
            or obj2._meta.app_label in self.route_app_labels
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
