from collections.abc import Sequence
from typing import Any

from django.db.backends.postgresql.operations import (
    DatabaseOperations as PostgresDatabaseOperations,
)

# Tables holding migration-seeded reference data that must survive `flush`.
#
# TODO: remove this backend once https://github.com/Flagsmith/flagsmith/issues/7850 is closed
PRESERVED_TABLES = frozenset({"permissions_permissionmodel"})


class DatabaseOperations(PostgresDatabaseOperations):
    def sql_flush(
        self,
        style: Any,
        tables: Sequence[str],
        *,
        reset_sequences: bool = False,
        allow_cascade: bool = False,
    ) -> list[str]:
        retained = [table for table in tables if table not in PRESERVED_TABLES]
        return super().sql_flush(
            style,
            retained,
            reset_sequences=reset_sequences,
            allow_cascade=allow_cascade,
        )
