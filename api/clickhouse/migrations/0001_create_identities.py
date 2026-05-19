from django.db import migrations


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


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False
    initial = True

    operations = [
        migrations.RunSQL(_SCHEMA_DDL, reverse_sql="DROP TABLE IF EXISTS IDENTITIES"),
    ]
