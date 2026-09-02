import importlib

from django.apps import AppConfig
from django.conf import settings

# Importing this module applies `clickhouse-backend`'s monkeypatches to Django
# internals as an import side effect.
CLICKHOUSE_BACKEND_MODULE = "clickhouse_backend.backend"


class ClickHouseConfig(AppConfig):
    name = "clickhouse"
    label = "clickhouse"

    def ready(self) -> None:
        if "clickhouse" not in settings.DATABASES:
            # Postgres-only install. This app stays installed so the router can
            # fence its migrations off the default database, but there is no
            # ClickHouse connection to patch Django for.
            return

        # Django would otherwise import the backend -- and so apply the
        # patches -- only when it first opens a ClickHouse connection. One of
        # them replaces `MigrationRecorder.Migration` with a property that
        # caches the model per recorder instance, whereas Django's own
        # `classproperty` caches the Postgres-shaped model on the *class*. So
        # if anything touches a Postgres recorder before the patch lands, the
        # ClickHouse recorder is handed a model with no `deleted` column, and
        # `migration_qs` -- which filters on `deleted` for ClickHouse
        # connections -- fails with `FieldError: Cannot resolve keyword
        # 'deleted' into field`. Patch during startup so ordering cannot
        # matter.
        importlib.import_module(CLICKHOUSE_BACKEND_MODULE)
