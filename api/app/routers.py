class AnalyticsRouter:
    route_app_labels = ["app_analytics"]

    def db_for_read(self, model, **hints):  # type: ignore[no-untyped-def]
        """
        Attempts to read analytics models go to 'analytics' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def db_for_write(self, model, **hints):  # type: ignore[no-untyped-def]
        """
        Attempts to write analytics models go to 'analytics' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "analytics"
        return None

    def allow_relation(self, obj1, obj2, **hints):  # type: ignore[no-untyped-def]
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

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # type: ignore[no-untyped-def]
        """
        Make sure the analytics app only appears in the 'analytics' database
        """
        if app_label in self.route_app_labels:
            if db != "default":
                return db == "analytics"
        return None
