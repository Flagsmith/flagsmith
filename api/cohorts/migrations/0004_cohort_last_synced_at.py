from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cohorts", "0003_cohort_sync_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohort",
            name="last_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
