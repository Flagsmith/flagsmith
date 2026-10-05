from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.utils import timezone


def soft_delete_snowflake_connections(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    WarehouseConnection = apps.get_model("experimentation", "WarehouseConnection")
    WarehouseConnection.objects.filter(
        warehouse_type="snowflake",
        deleted_at__isnull=True,
    ).update(deleted_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0016_add_delivery_connections_db_view_and_status"),
    ]

    operations = [
        migrations.RunPython(
            soft_delete_snowflake_connections,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="warehouseconnection",
            name="warehouse_type",
            field=models.CharField(
                choices=[("flagsmith", "Flagsmith"), ("clickhouse", "ClickHouse")],
                max_length=50,
            ),
        ),
    ]
