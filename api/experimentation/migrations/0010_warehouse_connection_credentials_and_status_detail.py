from django.db import migrations, models

import experimentation.fields


class Migration(migrations.Migration):
    dependencies = [
        ("experimentation", "0009_add_rollout_segment"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouseconnection",
            name="credentials",
            field=experimentation.fields.EncryptedJSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="warehouseconnection",
            name="status_detail",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
