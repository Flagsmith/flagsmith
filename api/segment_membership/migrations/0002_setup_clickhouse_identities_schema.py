"""Create the canonical IDENTITIES table the SQL flag engine emits
against when a ClickHouse cluster is configured.

The engine's published `ClickHouseDialect.schema_ddl` is `MergeTree`
with five columns — the "simplest correct shape" for any consumer.
The PoC overrides to `ReplacingMergeTree(inserted_at)` over
`(environment_id, id)` plus an `inserted_at` version column: daily
backfill INSERTs into the same primary key get deduplicated at merge
time (most-recent `inserted_at` wins), and the refresh task adds
`FROM IDENTITIES FINAL` for strict reads. The translator's emitted
predicates are engine-agnostic and work unchanged.

No-op when `CLICKHOUSE_ENABLED` is False, so self-hosted installs
without ClickHouse (and the test suite) migrate cleanly.
"""

from django.conf import settings
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

from segment_membership.services import open_clickhouse_client

_SCHEMA_DDL = """\
CREATE TABLE IF NOT EXISTS IDENTITIES (
    -- environment.key from EnvironmentContext; used as the env partition
    environment_id String,

    -- stable per-identity row id derived from identity_uuid bytes (signed 64-bit)
    id UInt64,

    -- the identity's external identifier, exposed as $.identity.identifier
    identifier String,

    -- the composite identity key, exposed as $.identity.key
    identity_key String,

    -- the identity's full trait map. ClickHouse's `JSON` type stores each
    -- path as a typed subcolumn so trait lookups are columnar reads, not
    -- per-row JSON parses. SQL NULL for an identity with no traits.
    traits JSON,

    -- version column for ReplacingMergeTree dedup. Defaults to insert time
    -- so the most-recent backfill of a given (environment_id, id) wins.
    inserted_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(inserted_at)
ORDER BY (environment_id, id)
"""


def setup_clickhouse_identities_schema(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    if not settings.CLICKHOUSE_ENABLED:
        return
    with open_clickhouse_client() as client:
        client.command(_SCHEMA_DDL)


class Migration(migrations.Migration):
    # The ClickHouse DDL talks to a remote service; running it inside
    # Django's default-atomic migration block would couple this Postgres
    # migration to a ClickHouse transaction we don't actually need.
    atomic = False

    dependencies = [
        ("segment_membership", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            setup_clickhouse_identities_schema,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
