import typing

import pytest
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.base.creation import BaseDatabaseCreation
from django.test import override_settings

from tests.migration_snapshots import (
    MaintenanceConnection,
    MigrationSnapshots,
    migration_graph_digest,
)


@pytest.fixture()
def maintenance(db: None) -> typing.Generator[MaintenanceConnection, None, None]:
    """A connection that can create and drop databases, as the cache uses."""
    connection = MaintenanceConnection(DEFAULT_DB_ALIAS)
    yield connection
    connection.close()


@pytest.fixture()
def template_name_for_graph(
    db: None,
) -> typing.Callable[[str], str]:
    """Name a template as the cache would, for a given migration graph digest.

    Deliberately suffixed `probe` rather than `latest` or a plan depth: those
    are the names the cache really uses, and a test that dropped one would pull
    the database out from under every other xdist worker.
    """

    def name_for(digest: str) -> str:
        base = connections[DEFAULT_DB_ALIAS].settings_dict["NAME"].split("_gw")[0]
        return f"{base}_migsnap_{digest}_probe"

    return name_for


def test_migration_snapshots__template_from_another_graph__is_dropped(
    db: None,
    maintenance: MaintenanceConnection,
    template_name_for_graph: typing.Callable[[str], str],
) -> None:
    """Templates only stay useful while their migrations do.

    A working copy that visits a branch with different migrations leaves a
    template behind that can never be cloned again, so opening the cache drops
    it. Without this, every branch a developer checks out would cost another
    copy of the database.
    """
    # Given
    stale = template_name_for_graph("0ldgr4ph")
    current = template_name_for_graph(migration_graph_digest())
    for name in (stale, current):
        maintenance.execute(f'DROP DATABASE IF EXISTS "{name}"')
        maintenance.execute(f'CREATE DATABASE "{name}"')

    # When
    snapshots = MigrationSnapshots(DEFAULT_DB_ALIAS)

    # Then
    try:
        remaining = {
            name
            for (name,) in maintenance.fetch(
                "SELECT datname FROM pg_database WHERE datname IN (%s, %s)",
                (stale, current),
            )
        }
        assert remaining == {current}
    finally:
        snapshots.close()
        maintenance.execute(f'DROP DATABASE IF EXISTS "{current}"')


def test_migration_graph_digest__app_without_migrations__is_excluded() -> None:
    # Given
    migration_graph_digest.cache_clear()
    baseline = migration_graph_digest()

    # When
    migration_graph_digest.cache_clear()
    with override_settings(MIGRATION_MODULES={"segments": None}):
        without_segments = migration_graph_digest()
    migration_graph_digest.cache_clear()

    # Then
    assert without_segments != baseline
    assert migration_graph_digest() == baseline


def test_deserialize_db_from_string__snapshots_in_use__explains_itself() -> None:
    # Given
    creation = connections[DEFAULT_DB_ALIAS].creation

    # When
    with pytest.raises(NotImplementedError) as exc_info:
        BaseDatabaseCreation.deserialize_db_from_string(creation, "[]")

    # Then
    assert "serialized_rollback is unsupported" in str(exc_info.value)
