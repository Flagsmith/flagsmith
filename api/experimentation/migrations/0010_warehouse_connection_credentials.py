from django.db import migrations

import core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("experimentation", "0009_add_rollout_segment"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouseconnection",
            name="credentials",
            field=core.fields.EncryptedJSONField(blank=True, null=True),
        ),
    ]
