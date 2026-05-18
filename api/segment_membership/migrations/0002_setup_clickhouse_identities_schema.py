"""Create the IDENTITIES table the SQL flag engine reads against.

Overrides the engine's published `MergeTree` schema with
`ReplacingMergeTree(inserted_at)` over `(environment_id, id)` so daily
re-INSERTs dedupe by most-recent `inserted_at` at merge time, with
`FROM IDENTITIES FINAL` covering reads in between merges. No-op when
`CLICKHOUSE_ENABLED` is False so installs without ClickHouse migrate
cleanly.
"""

from django.conf import settings
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

from segment_membership.services import open_clickhouse_client

_SCHEMA_DDL = """\
CREATE TABLE IF NOT EXISTS IDENTITIES (
    environment_id String,
    -- UInt64 because we derive from UUID bytes; signed would refuse negatives.
    id UInt64,
    identifier String,
    identity_key String,
    -- Stored per top-level key as typed subcolumns; SQL NULL for empty traits.
    traits JSON,
    -- ReplacingMergeTree version column; most-recent insert wins per PK.
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
    # Disable Django's atomic wrapper — the DDL runs against a remote service.
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
