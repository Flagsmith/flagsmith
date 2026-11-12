from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0017_add_databricks_warehouse_type"),
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
                    ("postgres", "PostgreSQL"),
                ],
                max_length=50,
            ),
        ),
    ]
