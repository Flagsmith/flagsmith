from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0016_add_delivery_connections_db_view_and_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="warehouseconnection",
            name="warehouse_type",
            field=models.CharField(
                choices=[
                    ("flagsmith", "Flagsmith"),
                    ("snowflake", "Snowflake"),
                    ("clickhouse", "ClickHouse"),
                    ("databricks", "Databricks"),
                ],
                max_length=50,
            ),
        ),
    ]
