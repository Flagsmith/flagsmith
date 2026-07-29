from django.db import migrations

_FORWARD_DDL = """\
ALTER TABLE IDENTITIES
    ADD COLUMN IF NOT EXISTS ingested_at DateTime DEFAULT now(),
    ADD COLUMN IF NOT EXISTS source LowCardinality(String) DEFAULT 'backfill'
"""

_REVERSE_DDL = """\
ALTER TABLE IDENTITIES
    DROP COLUMN IF EXISTS ingested_at,
    DROP COLUMN IF EXISTS source
"""


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False

    dependencies = [
        ("clickhouse", "0001_create_identities"),
    ]

    operations = [
        migrations.RunSQL(_FORWARD_DDL, reverse_sql=_REVERSE_DDL),
    ]
