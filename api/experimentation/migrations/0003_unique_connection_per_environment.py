from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experimentation", "0002_add_config_and_created_status"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="warehouseconnection",
            name="unique_active_warehouse_per_type_and_env",
        ),
        migrations.AddConstraint(
            model_name="warehouseconnection",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("environment",),
                name="unique_active_warehouse_per_env",
            ),
        ),
    ]
