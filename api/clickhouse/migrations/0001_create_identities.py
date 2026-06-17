from django.db import migrations


_SCHEMA_DDL = """\
CREATE TABLE IF NOT EXISTS IDENTITIES (
    environment_id String,
    -- (environment_id, identifier) is the natural unique key in Flagsmith's
    -- identity model — dedupes ReplacingMergeTree without a synthetic id.
    identifier String,
    identity_key String,
    -- Stored per top-level key as typed subcolumns; SQL NULL for empty traits.
    traits JSON,
    -- ReplacingMergeTree version column; most-recent insert wins per PK.
    inserted_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(inserted_at)
ORDER BY (environment_id, identifier)
"""


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False
    initial = True

    operations = [
        migrations.RunSQL(_SCHEMA_DDL, reverse_sql="DROP TABLE IF EXISTS IDENTITIES"),
    ]
