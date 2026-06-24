from clickhouse_backend.backend.base import (
    DatabaseWrapper as ClickHouseDatabaseWrapper,
)

from core.db_backends.clickhouse.creation import DatabaseCreation


class DatabaseWrapper(ClickHouseDatabaseWrapper):  # type: ignore[misc]
    creation_class = DatabaseCreation
