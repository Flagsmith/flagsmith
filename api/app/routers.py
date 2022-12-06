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
        """
        All non-auth models end up in this pool.
        """
        return db == "default"
