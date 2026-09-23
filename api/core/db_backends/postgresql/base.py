from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)

from core.db_backends.postgresql.operations import DatabaseOperations


class DatabaseWrapper(PostgresDatabaseWrapper):
    ops_class = DatabaseOperations
