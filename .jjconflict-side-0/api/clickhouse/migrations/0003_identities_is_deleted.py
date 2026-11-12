from django.db import migrations

_FORWARD_DDL = """\
ALTER TABLE IDENTITIES
    ADD COLUMN IF NOT EXISTS is_deleted Bool DEFAULT false
"""

_REVERSE_DDL = """\
ALTER TABLE IDENTITIES
    DROP COLUMN IF EXISTS is_deleted
"""


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False

    dependencies = [
        ("clickhouse", "0002_identities_ingested_at_and_source"),
    ]

    operations = [
        migrations.RunSQL(_FORWARD_DDL, reverse_sql=_REVERSE_DDL),
    ]
