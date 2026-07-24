from django.db import migrations

_CREATE_WATERMARK_TABLE = """\
CREATE TABLE IF NOT EXISTS IDENTITIES_ENV_WATERMARK (
    environment_id String,
    watermark AggregateFunction(max, DateTime)
)
ENGINE = AggregatingMergeTree
ORDER BY environment_id
"""

_CREATE_WATERMARK_MV = """\
CREATE MATERIALIZED VIEW IF NOT EXISTS IDENTITIES_ENV_WATERMARK_MV
TO IDENTITIES_ENV_WATERMARK
AS
SELECT environment_id, maxState(inserted_at) AS watermark
FROM IDENTITIES
GROUP BY environment_id
"""

_BACKFILL_WATERMARK = """\
INSERT INTO IDENTITIES_ENV_WATERMARK
SELECT environment_id, maxState(inserted_at) AS watermark
FROM IDENTITIES
GROUP BY environment_id
"""


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False

    dependencies = [
        ("clickhouse", "0003_identities_is_deleted"),
    ]

    operations = [
        migrations.RunSQL(
            _CREATE_WATERMARK_TABLE,
            reverse_sql="DROP TABLE IF EXISTS IDENTITIES_ENV_WATERMARK",
        ),
        migrations.RunSQL(
            _CREATE_WATERMARK_MV,
            reverse_sql="DROP TABLE IF EXISTS IDENTITIES_ENV_WATERMARK_MV",
        ),
        migrations.RunSQL(_BACKFILL_WATERMARK, reverse_sql=migrations.RunSQL.noop),
    ]
