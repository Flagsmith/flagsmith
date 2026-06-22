from clickhouse_backend.backend.creation import (
    DatabaseCreation as ClickHouseDatabaseCreation,
)


class DatabaseCreation(ClickHouseDatabaseCreation):  # type: ignore[misc]
    """ClickHouse test-database creation with parallel-clone support.

    ClickHouse has no transactional rollback, so each xdist worker needs its own physical
    database for isolation, mirroring how the Postgres backend clones the
    primary test database per worker.

    TODO Remove this subclass once https://github.com/jayvynl/django-clickhouse-backend/issues/167
    ships.
    """

    def _clone_test_db(
        self,
        suffix: str,
        verbosity: int,
        keepdb: bool = False,
    ) -> None:
        source_database_name: str = self.connection.settings_dict["NAME"]
        target_database_name: str = self.get_test_db_clone_settings(suffix)["NAME"]
        quote_name = self.connection.ops.quote_name

        with self._nodb_cursor() as cursor:
            cursor.execute(
                f"DROP DATABASE IF EXISTS {quote_name(target_database_name)} SYNC"
            )
            cursor.execute(f"CREATE DATABASE {quote_name(target_database_name)}")
            # Recreate every source table as an empty copy; `CREATE TABLE ... AS`
            # copies the engine and schema without any rows.
            cursor.execute(
                "SELECT name FROM system.tables WHERE database = %s",
                [source_database_name],
            )
            for (table_name,) in cursor.fetchall():
                cursor.execute(
                    f"CREATE TABLE "
                    f"{quote_name(target_database_name)}.{quote_name(table_name)} "
                    f"AS {quote_name(source_database_name)}.{quote_name(table_name)}"
                )
