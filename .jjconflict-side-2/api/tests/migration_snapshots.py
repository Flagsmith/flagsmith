import contextlib
import functools
import hashlib
import importlib.util
import pathlib
import typing

from django.apps import apps
from django.apps.config import AppConfig
from django.conf import settings as django_settings
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.base.base import NO_DB_ALIAS
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django_test_migrations import sql
from django_test_migrations.logic.migrations import normalize
from django_test_migrations.migrator import Migrator
from django_test_migrations.plan import truncate_plan
from django_test_migrations.types import MigrationPlan, MigrationSpec

# Length of the migration graph digest embedded in template database names.
# Eight hex characters comfortably separate the handful of graphs a working
# copy sees while keeping names well inside PostgreSQL's 63 byte limit.
_DIGEST_LENGTH = 8

# Shared by every template this module manages, so they are easy to recognise
# in `psql -l` and safe to drop wholesale.
_TEMPLATE_INFIX = "migsnap"

# Key for the state in which the whole history has been applied.
_LATEST = "latest"


class SnapshotsUnavailable(Exception):
    """Raised when the database cannot back migration state snapshots."""


class MaintenanceConnection:
    """A connection to the maintenance database, for `CREATE`/`DROP DATABASE`.

    Implemented as a session-long equivalent of Django's `_nodb_cursor`.
    """

    def __init__(self, alias: str) -> None:
        base = connections[alias]
        self._connection = base.__class__(
            {**base.settings_dict, "NAME": None}, alias=NO_DB_ALIAS
        )

    def execute(self, statement: str, params: typing.Sequence[typing.Any] = ()) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(statement, params)

    def fetch(
        self,
        statement: str,
        params: typing.Sequence[typing.Any] = (),
    ) -> list[tuple[typing.Any, ...]]:
        with self._connection.cursor() as cursor:
            cursor.execute(statement, params)
            return list(cursor.fetchall())

    def close(self) -> None:
        self._connection.close()


@functools.cache
def migration_graph_digest() -> str:
    """Digest the migration files, avoiding `MigrationLoader`'s costly module imports."""
    digest = hashlib.sha256()
    paths = sorted(
        (app_config.label, path)
        for app_config in apps.get_app_configs()
        for path in _iter_migration_paths(app_config)
    )
    for label, path in paths:
        digest.update(f"{label}/{path.name}".encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:_DIGEST_LENGTH]


class MigrationSnapshots:
    """Template databases holding migration states for one database alias.

    Replaying migrations is slow; copying a database is not. So each state we
    reach is saved as a template, and asked-for states are cloned from one.

    A state is keyed by how many migrations it has applied, which makes the
    templates nest: to reach state N, clone the deepest template below it and
    replay only what is missing.

    Template names carry a digest of the migration files, so editing a
    migration -- or switching branch -- builds new templates instead of
    handing anyone a stale schema. Templates from old digests are dropped.
    """

    def __init__(self, alias: str, database_name: str | None = None) -> None:
        connection = connections[alias]
        if connection.vendor != "postgresql":  # pragma: no cover
            raise SnapshotsUnavailable(
                f"Migration state snapshots need PostgreSQL, got {connection.vendor!r}"
            )
        self._alias = alias
        self._maintenance = MaintenanceConnection(alias)
        self._database_name = database_name or connection.settings_dict["NAME"]
        self._namespace = self._build_namespace()
        self._cached: set[str] = set()
        self._discover()

    @property
    def _base_name(self) -> str:
        # Drop any xdist worker suffix: every worker migrates the same graph
        return self._database_name.split("_gw")[0]

    def _build_namespace(self) -> str:
        return f"{self._base_name}_{_TEMPLATE_INFIX}_{migration_graph_digest()}"

    def _template_name(self, key: int | str) -> str:
        return f"{self._namespace}_{key}"

    def _discover(self) -> None:
        """Load the usable templates, dropping any left by an older graph.

        Scoped to this database's own templates.
        """
        rows = self._maintenance.fetch(
            "SELECT datname FROM pg_database WHERE datname LIKE %s",
            (f"{self._base_name}\\_{_TEMPLATE_INFIX}\\_%",),
        )
        for (name,) in rows:
            if name.startswith(f"{self._namespace}_"):
                self._cached.add(name)
            else:
                # Built from a migration graph that no longer exists; drop it.
                self._drop(name)

    def _drop(self, name: str) -> None:
        # A template another worker is cloning right now cannot be dropped;
        # whoever comes next will clean it up.
        with contextlib.suppress(Exception):
            self._maintenance.execute(f'DROP DATABASE IF EXISTS "{name}"')

    def _copy(self, source: str, target: str) -> None:
        # PostgreSQL refuses to copy or drop a database that has sessions attached; kill them.
        self._maintenance.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname IN (%s, %s) AND pid <> pg_backend_pid()",
            (source, target),
        )
        self._maintenance.execute(f'DROP DATABASE IF EXISTS "{target}"')
        self._maintenance.execute(f'CREATE DATABASE "{target}" TEMPLATE "{source}"')

    def _advisory_lock(self, *, shared: bool) -> typing.ContextManager[None]:
        return _advisory_lock(self._maintenance, self._namespace, shared=shared)

    def exclusive(self) -> typing.ContextManager[None]:
        """Hold this namespace's lock for writing."""
        return self._advisory_lock(shared=False)

    def refresh(self) -> None:
        """Re-read which templates exist, e.g. after waiting on the lock."""
        self._cached.clear()
        self._discover()

    def has(self, key: int | str) -> bool:
        return self._template_name(key) in self._cached

    def nearest_ancestor(self, depth: int) -> int | None:
        """Return the deepest cached prefix strictly shorter than `depth`."""
        prefix = f"{self._namespace}_"
        candidates = [
            int(suffix)
            for name in self._cached
            if (suffix := name[len(prefix) :]).isdigit() and int(suffix) < depth
        ]
        return max(candidates, default=None)

    def restore(self, key: int | str) -> None:
        """Replace the working database with the cached state at `key`."""
        connections[self._alias].close()
        with self._advisory_lock(shared=True):
            self._copy(self._template_name(key), self._database_name)

    def save(self, key: int | str) -> None:
        """Cache the working database's current state under `key`."""
        name = self._template_name(key)
        connections[self._alias].close()
        with self.exclusive():
            self._copy(self._database_name, name)
        self._cached.add(name)

    def close(self) -> None:
        self._maintenance.close()


class ClickHouseSnapshots:
    """Template databases holding migration states for one database alias.

    Clickhouse-specific implementation relying on `CREATE TABLE ... AS ...`."""

    _MIGRATIONS_TABLE = "django_migrations"

    def __init__(self, alias: str, database_name: str | None = None) -> None:
        self._alias = alias
        self._database_name = database_name or connections[alias].settings_dict["NAME"]
        base = self._database_name.split("_gw")[0]
        self._template = f"{base}_{_TEMPLATE_INFIX}_{migration_graph_digest()}"
        # ClickHouse has no advisory locks, so borrow PostgreSQL's.
        self._maintenance = MaintenanceConnection(DEFAULT_DB_ALIAS)

    def exclusive(self) -> typing.ContextManager[None]:
        """Hold this template's lock for writing. See `MigrationSnapshots`."""
        return _advisory_lock(self._maintenance, self._template, shared=False)

    def shared(self) -> typing.ContextManager[None]:
        """Hold this template's lock for reading, to clone it."""
        return _advisory_lock(self._maintenance, self._template, shared=True)

    def _quote(self, name: str) -> str:
        return connections[self._alias].ops.quote_name(name)

    @contextlib.contextmanager
    def _cursor(self) -> typing.Iterator[typing.Any]:
        connection = connections[self._alias]
        with connection._nodb_cursor() as cursor:  # noqa: SLF001
            yield cursor

    def _databases(self) -> set[str]:
        with self._cursor() as cursor:
            cursor.execute("SELECT name FROM system.databases")
            return {name for (name,) in cursor.fetchall()}

    def has(self, key: int | str) -> bool:
        del key  # ClickHouse only ever caches the fully migrated state.
        return self._template in self._databases()

    def _copy(self, source: str, target: str) -> None:
        with self._cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {self._quote(target)} SYNC")
            cursor.execute(f"CREATE DATABASE {self._quote(target)}")
            cursor.execute(
                "SELECT name FROM system.tables WHERE database = %s", [source]
            )
            for (table,) in cursor.fetchall():
                cursor.execute(
                    f"CREATE TABLE {self._quote(target)}.{self._quote(table)} "
                    f"AS {self._quote(source)}.{self._quote(table)}"
                )
            # Make sure the database is seen as migrated.
            migrations = self._quote(self._MIGRATIONS_TABLE)
            cursor.execute(
                f"INSERT INTO {self._quote(target)}.{migrations} "
                f"SELECT * FROM {self._quote(source)}.{migrations}"
            )

    def restore(self, key: int | str) -> None:
        del key
        connections[self._alias].close()
        with self.shared():
            self._copy(self._template, self._database_name)

    def save(self, key: int | str) -> None:
        del key
        connections[self._alias].close()
        with self.exclusive():
            self._copy(self._database_name, self._template)

    def close(self) -> None:
        self._maintenance.close()


class SnapshotMigrator(Migrator):
    """A `Migrator` that clones cached states instead of replaying migrations."""

    def __init__(self, database: str | None, snapshots: MigrationSnapshots) -> None:
        super().__init__(database)
        self._snapshots = snapshots

    def _full_plan(self) -> MigrationPlan:
        self._executor.loader.build_graph()  # reload
        return self._executor.migration_plan(
            self._executor.loader.graph.leaf_nodes(),
            clean_start=True,
        )

    def apply_initial_migration(self, targets: MigrationSpec) -> ProjectState:
        migration_targets = normalize(targets)
        depth = len(truncate_plan(migration_targets, self._full_plan()))

        if self._snapshots.has(depth):
            self._snapshots.restore(depth)
            return self._restored_project_state()

        ancestor = self._snapshots.nearest_ancestor(depth)
        if ancestor is None:
            sql.drop_models_tables(self._database, no_style())
            sql.flush_django_migrations_table(self._database, no_style())
            ancestor = 0
            self._snapshots.save(ancestor)
        else:
            self._snapshots.restore(ancestor)

        # Replay only the migrations between the state we restored and the one
        # under test. Rebuilding the plan first refreshes the executor's view
        # of what the restored database has applied.
        plan = self._full_plan()[ancestor:depth]
        state = self._migrate(migration_targets, plan=plan)
        self._snapshots.save(depth)
        return state

    def reset(self) -> None:
        """Restore the fully migrated state the rest of the suite expects."""
        self._snapshots.restore(_LATEST)

    def _restored_project_state(self) -> ProjectState:
        """Build the model state matching the migrations the database records.

        Cloning a template leaves `django_migrations` exactly as the snapshot
        had it, so the applied set is the source of truth and no migration has
        to run to derive the historical models.
        """
        self._executor.loader.build_graph()
        state: ProjectState = self._executor._create_project_state(  # type: ignore[attr-defined]
            with_applied_migrations=True,
        )
        state.clear_delayed_apps_cache()
        return state


def build_snapshots(alias: str = DEFAULT_DB_ALIAS) -> MigrationSnapshots:
    """Open the snapshot cache for `alias`, recording the migrated state."""
    snapshots = MigrationSnapshots(alias)
    if not snapshots.has(_LATEST):
        # Only reachable when the test database was not created through
        # `template_backed_test_databases`, e.g. under `--reuse-db`.
        with snapshots.exclusive():  # pragma: no cover
            snapshots.refresh()
            if not snapshots.has(_LATEST):
                snapshots.save(_LATEST)
    return snapshots


@contextlib.contextmanager
def template_backed_test_databases() -> typing.Iterator[None]:
    """Make Django build test databases by cloning a migrated template.

    The first caller to arrive migrates and leaves a template behind; everyone
    after that -- later xdist workers, later runs, other branches on the same
    migration graph -- clones it.
    """
    original = BaseDatabaseCreation.create_test_db

    def create_test_db(
        self: BaseDatabaseCreation,
        verbosity: int = 1,
        autoclobber: bool = False,
        serialize: bool = True,
        keepdb: bool = False,
    ) -> str:
        alias = self.connection.alias
        test_database_name: str = self._get_test_db_name()  # type: ignore[attr-defined]

        snapshots: MigrationSnapshots | ClickHouseSnapshots
        if self.connection.vendor == "clickhouse":
            snapshots = ClickHouseSnapshots(alias, database_name=test_database_name)
        else:
            try:
                snapshots = MigrationSnapshots(alias, database_name=test_database_name)
            except SnapshotsUnavailable:  # pragma: no cover
                return original(self, verbosity, autoclobber, serialize, keepdb)

        try:
            if not snapshots.has(_LATEST):
                # Serialise template construction across xdist workers.
                with snapshots.exclusive():
                    if isinstance(snapshots, MigrationSnapshots):
                        snapshots.refresh()
                    # Another worker may have built the template while we
                    # waited for the lock, in which case cloning it is still
                    # hundreds of times cheaper than migrating.
                    if not snapshots.has(_LATEST):
                        name = original(self, verbosity, autoclobber, serialize, keepdb)
                        snapshots.save(_LATEST)
                        return name

            snapshots.restore(_LATEST)
            self.connection.close()
            django_settings.DATABASES[alias]["NAME"] = test_database_name
            self.connection.settings_dict["NAME"] = test_database_name
            self.connection.ensure_connection()
            return test_database_name
        finally:
            snapshots.close()

    def serialize_db_to_string(self: BaseDatabaseCreation) -> str:
        """Refuse the setup-time snapshot Django takes for `serialized_rollback`.

        Django serialises every model in every database while setting the
        databases up, so that `TransactionTestCase(serialized_rollback=True)`
        can restore them afterwards.

        No-op instead, sacrificing the ability to use `serialized_rollback=True`
        (which we'll never need anyway.)
        """
        return ""

    def deserialize_db_from_string(self: BaseDatabaseCreation, data: str) -> None:
        raise NotImplementedError(
            "serialized_rollback is unsupported: the test databases are cloned "
            "from templates and never serialised. See tests/migration_snapshots.py."
        )

    original_serialize = BaseDatabaseCreation.serialize_db_to_string
    original_deserialize = BaseDatabaseCreation.deserialize_db_from_string
    BaseDatabaseCreation.create_test_db = create_test_db  # type: ignore[method-assign]
    BaseDatabaseCreation.serialize_db_to_string = serialize_db_to_string  # type: ignore[method-assign]
    BaseDatabaseCreation.deserialize_db_from_string = deserialize_db_from_string  # type: ignore[method-assign]
    try:
        yield
    finally:
        BaseDatabaseCreation.create_test_db = original  # type: ignore[method-assign]
        BaseDatabaseCreation.serialize_db_to_string = original_serialize  # type: ignore[method-assign]
        BaseDatabaseCreation.deserialize_db_from_string = original_deserialize  # type: ignore[method-assign]


def _iter_migration_paths(app_config: AppConfig) -> typing.Iterable[pathlib.Path]:
    module_name, _ = MigrationLoader.migrations_module(app_config.label)
    if module_name is None:
        return
    if spec := importlib.util.find_spec(module_name):
        if search_locations := spec.submodule_search_locations:
            for location in search_locations:
                for path in pathlib.Path(location).glob("*.py"):
                    yield path


@contextlib.contextmanager
def _advisory_lock(
    maintenance: MaintenanceConnection,
    namespace: str,
    *,
    shared: bool,
) -> typing.Iterator[None]:
    """Hold a PostgreSQL advisory lock naming `namespace`."""
    mode = "_shared" if shared else ""
    maintenance.execute(f"SELECT pg_advisory_lock{mode}(hashtext(%s))", (namespace,))
    try:
        yield
    finally:
        maintenance.execute(
            f"SELECT pg_advisory_unlock{mode}(hashtext(%s))", (namespace,)
        )
