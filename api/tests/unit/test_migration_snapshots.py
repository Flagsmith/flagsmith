import typing

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from tests.migration_snapshots import (
    MigrationSnapshots,
    _MaintenanceConnection,
    migration_graph_digest,
)


@pytest.fixture()
def maintenance(db: None) -> typing.Generator[_MaintenanceConnection, None, None]:
    """A connection that can create and drop databases, as the cache uses."""
    connection = _MaintenanceConnection(DEFAULT_DB_ALIAS)
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
    maintenance: _MaintenanceConnection,
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
