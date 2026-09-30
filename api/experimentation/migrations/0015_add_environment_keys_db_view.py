from pathlib import Path

from django.db import migrations

from core.migration_helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):
    dependencies = [
        ("environments", "0039_use_no_ssrf_url_field"),
        ("experimentation", "0014_drop_ingestion_infrastructure_and_delivery_log"),
    ]

    operations = [
        PostgresOnlyRunSQL.from_sql_file(
            Path(__file__).parent / "sql" / "0015_create_environment_keys_db_view.sql",
            reverse_sql="DROP VIEW IF EXISTS experimentation_environment_keys;",
        ),
    ]
