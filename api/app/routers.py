from typing import Any, Literal

from django.db.models import Model

AnalyticsDatabaseName = Literal["analytics"]


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
        """Ensure analytics models get created on the right database"""
        if app_label in self.route_app_labels:
            if db != "default":
                return db == "analytics"
        return None
