from pathlib import Path

from django.db import migrations

from core.migration_helpers import PostgresOnlyRunSQL

SQL_DIR = Path(__file__).parent / "sql"


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0018_add_postgres_warehouse_type"),
    ]

    operations = [
        PostgresOnlyRunSQL.from_sql_file(
            SQL_DIR / "0019_create_flagsmith_database_events_table.sql",
            reverse_sql=migrations.RunSQL.noop,
        ),
        PostgresOnlyRunSQL(
            (
                SQL_DIR
                / "0019_exclude_flagsmith_database_connections_from_delivery_db_view.sql"
            ).read_text(),
            reverse_sql="DROP VIEW IF EXISTS experimentation_delivery_connections;\n"
            + (SQL_DIR / "0016_create_delivery_connections_db_view.sql").read_text(),
        ),
    ]
