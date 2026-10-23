from pathlib import Path

import django.db.models.deletion
from django.db import migrations, models

from core.migration_helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0015_add_environment_keys_db_view"),
    ]

    operations = [
        migrations.CreateModel(
            name="WarehouseDeliveryStatus",
            fields=[
                (
                    "connection",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="delivery_status",
                        serialize=False,
                        to="experimentation.warehouseconnection",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("pending_connection", "Pending Connection"),
                            ("connected", "Connected"),
                            ("errored", "Errored"),
                        ],
                        max_length=50,
                    ),
                ),
                ("detail", models.TextField(blank=True, null=True)),
                ("updated_at", models.DateTimeField()),
            ],
        ),
        PostgresOnlyRunSQL.from_sql_file(
            Path(__file__).parent
            / "sql"
            / "0016_create_delivery_connections_db_view.sql",
            reverse_sql="DROP VIEW IF EXISTS experimentation_delivery_connections;",
        ),
    ]
