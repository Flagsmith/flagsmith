from django.db import migrations

_ADD_COLUMN_DDL = (
    "ALTER TABLE IDENTITIES ADD COLUMN IF NOT EXISTS is_deleted Bool DEFAULT false"
)


class Migration(migrations.Migration):
    # ClickHouse has no transactional DDL.
    atomic = False
    dependencies = [("clickhouse", "0001_create_identities")]
    operations = [
        migrations.RunSQL(
            _ADD_COLUMN_DDL,
            reverse_sql=("ALTER TABLE IDENTITIES DROP COLUMN IF EXISTS is_deleted"),
        )
    ]
