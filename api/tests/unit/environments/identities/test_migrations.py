from django.db import connection
from django_test_migrations.migrator import Migrator


def _identity_identifier_idx_exists() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('identity_identifier_idx') IS NOT NULL")
        return bool(cursor.fetchone()[0])


def test_0008__index_exists__drops_it(migrator: Migrator) -> None:
    # Given
    migrator.apply_initial_migration(("identities", "0007_identity_system_traits"))
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute(
            "CREATE INDEX identity_identifier_idx ON environments_identity "
            "USING gin (UPPER(identifier) gin_trgm_ops)"
        )
    assert _identity_identifier_idx_exists()

    # When
    migrator.apply_tested_migration(
        ("identities", "0008_drop_identity_identifier_gin_index")
    )

    # Then
    assert not _identity_identifier_idx_exists()


def test_0008__index_does_not_exist__succeeds(migrator: Migrator) -> None:
    # Given
    migrator.apply_initial_migration(("identities", "0007_identity_system_traits"))
    assert not _identity_identifier_idx_exists()

    # When
    migrator.apply_tested_migration(
        ("identities", "0008_drop_identity_identifier_gin_index")
    )

    # Then
    assert not _identity_identifier_idx_exists()
